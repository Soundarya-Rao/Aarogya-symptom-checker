"""
Evaluation harness for the symptom assessment pipeline.

Runs a curated set of symptom descriptions with known expected severity
through assess_symptoms() and reports:
  - overall accuracy
  - confusion matrix (expected vs actual)
  - English RED-case recall
  - Non-English RED-case recall (tracked distinctly so non-English regressions cannot hide)
  - Combined RED-case recall

RED-case recall matters most here: classifying an actual emergency as
YELLOW/GREEN (a false negative) is the dangerous failure mode. Classifying
a mild case as RED (a false positive) just sends someone to a doctor
unnecessarily -- annoying, not dangerous. The two error types are NOT
equally bad, so overall accuracy alone would hide the failure that matters.

Usage:
    python eval/run_eval.py
"""

import json
import os
import sys
import time
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_client import assess_symptoms, LLMError  # noqa: E402

TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")
TEST_STATE = "Karnataka"  # state doesn't affect severity logic, held constant for the eval

# Pause between cases to respect free-tier rate limits (15 RPM) and prevent 429s.
SECONDS_BETWEEN_CASES = 3

UNICODE_SCRIPT_RANGES = {
    "Hindi": (0x0900, 0x097F),
    "Marathi": (0x0900, 0x097F),
    "Bengali": (0x0980, 0x09FF),
    "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
}

FOREIGN_RANGES = [
    (0x0530, 0x058F),  # Armenian
    (0x0400, 0x04FF),  # Cyrillic
    (0x0370, 0x03FF),  # Greek
    (0x10A0, 0x10FF),  # Georgian
    (0x0600, 0x06FF),  # Arabic
]

ALL_INDIC_RANGES = [
    (0x0900, 0x097F),  # Devanagari
    (0x0980, 0x09FF),  # Bengali
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
]


def check_script_integrity(assessment, language_name: str) -> tuple[bool, str]:
    """Returns (is_valid, reason) checking for language script correctness."""
    lang = language_name.strip()
    if lang.lower() in ("english", "en"):
        for ch in assessment.what_to_do:
            cp = ord(ch)
            if any(s <= cp <= e for s, e in ALL_INDIC_RANGES + FOREIGN_RANGES):
                return False, f"Non-English script detected: U+{cp:04X}"
        return True, "OK"

    expected_range = UNICODE_SCRIPT_RANGES.get(lang)
    if not expected_range:
        return True, "UNKNOWN_LANG"

    s_exp, e_exp = expected_range

    # 1. Count expected script characters in what_to_do
    exp_count = sum(1 for ch in assessment.what_to_do if s_exp <= ord(ch) <= e_exp)
    if exp_count < 5:
        return False, f"Expected {lang} script missing or too short (count={exp_count})"

    # 2. Check for explicitly foreign/corrupted scripts (Armenian, Cyrillic, etc.)
    full_text = assessment.what_to_do + " " + " ".join(assessment.possible_conditions)
    for ch in full_text:
        cp = ord(ch)
        for f_start, f_end in FOREIGN_RANGES:
            if f_start <= cp <= f_end:
                return False, f"Corrupted foreign script detected (U+{cp:04X})"

    # 3. Check for mismatched Indic scripts in what_to_do
    other_indic_ranges = [r for r in ALL_INDIC_RANGES if r != expected_range]
    other_indic_count = sum(1 for ch in assessment.what_to_do if any(s <= ord(ch) <= e for s, e in other_indic_ranges))
    if other_indic_count > 3:
        return False, f"Mismatched Indic script detected in {lang} (count={other_indic_count})"

    return True, "OK"


def run_eval():
    with open(TEST_CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    confusion = defaultdict(lambda: defaultdict(int))  # confusion[expected][actual] += 1
    
    lang_stats = defaultdict(lambda: {
        "total": 0,
        "severity_correct": 0,
        "script_correct": 0,
        "red_expected": 0,
        "red_correct": 0,
        "latencies": [],
        "script_failures": [],
    })

    print(f"Starting evaluation on {len(cases)} test cases across 8 languages...\n")

    for i, case in enumerate(cases, start=1):
        symptoms = case["symptoms"]
        expected = case["expected_severity"]
        lang = case.get("language", "English")

        t0 = time.time()
        script_ok = False
        script_reason = ""
        try:
            assessment = assess_symptoms(symptoms, TEST_STATE, language_name=lang)
            elapsed = time.time() - t0
            actual = assessment.severity
            script_ok, script_reason = check_script_integrity(assessment, lang)
        except (LLMError, ValueError) as e:
            elapsed = time.time() - t0
            actual = "ERROR"
            script_ok = False
            script_reason = str(e)
            print(f"[{i}] Pipeline error on: {symptoms!r} -> {e}")

        confusion[expected][actual] += 1
        
        # Track stats
        stats = lang_stats[lang]
        stats["total"] += 1
        stats["latencies"].append(elapsed)
        if actual == expected:
            stats["severity_correct"] += 1
        if script_ok:
            stats["script_correct"] += 1
        else:
            stats["script_failures"].append((symptoms[:40], script_reason))
        if expected == "RED":
            stats["red_expected"] += 1
            if actual == "RED":
                stats["red_correct"] += 1

        results.append({
            "symptoms": symptoms,
            "expected": expected,
            "actual": actual,
            "language": lang,
            "script_ok": script_ok,
            "script_reason": script_reason,
            "latency": elapsed,
        })
        
        sev_status = "OK" if actual == expected else f"MISMATCH(got {actual})"
        sc_status = "SCRIPT:OK" if script_ok else f"SCRIPT:FAIL({script_reason})"
        print(f"[{i:2d}/{len(cases)}] [{lang:9}] exp={expected:6} act={actual:6} [{sev_status:12}] [{sc_status}] ({elapsed:.2f}s)")

        if i < len(cases):
            time.sleep(SECONDS_BETWEEN_CASES)

    total = len(results)
    correct = sum(1 for r in results if r["actual"] == r["expected"])
    accuracy = correct / total if total else 0.0
    script_passes = sum(1 for r in results if r["script_ok"])
    script_rate = script_passes / total if total else 0.0

    # Separate English and Non-English metrics
    en_results = [r for r in results if r["language"].lower() in ("english", "en")]
    non_en_results = [r for r in results if r["language"].lower() not in ("english", "en")]

    en_red = [r for r in en_results if r["expected"] == "RED"]
    en_red_correct = sum(1 for r in en_red if r["actual"] == "RED")
    en_red_recall = en_red_correct / len(en_red) if en_red else float("nan")

    non_en_red = [r for r in non_en_results if r["expected"] == "RED"]
    non_en_red_correct = sum(1 for r in non_en_red if r["actual"] == "RED")
    non_en_red_recall = non_en_red_correct / len(non_en_red) if non_en_red else float("nan")

    all_red = [r for r in results if r["expected"] == "RED"]
    all_red_correct = sum(1 for r in all_red if r["actual"] == "RED")
    all_red_recall = all_red_correct / len(all_red) if all_red else float("nan")

    red_false_negatives = [r for r in all_red if r["actual"] != "RED"]

    print("\n" + "=" * 78)
    print("PER-LANGUAGE EVALUATION RESULTS")
    print("=" * 78)
    header = f"{'Language':12} | {'Cases':5} | {'Severity Acc':12} | {'RED Recall':11} | {'Script Integrity':16} | {'Avg Lat':7}"
    print(header)
    print("-" * 78)
    for lang, st in lang_stats.items():
        sev_acc = f"{st['severity_correct']}/{st['total']} ({st['severity_correct']/st['total']:.0%})"
        red_rec = f"{st['red_correct']}/{st['red_expected']} ({st['red_correct']/st['red_expected']:.0%})" if st['red_expected'] else "N/A"
        sc_rate = f"{st['script_correct']}/{st['total']} ({st['script_correct']/st['total']:.0%})"
        avg_l = f"{sum(st['latencies'])/len(st['latencies']):.2f}s" if st['latencies'] else "N/A"
        print(f"{lang:12} | {st['total']:5d} | {sev_acc:12} | {red_rec:11} | {sc_rate:16} | {avg_l:7}")

    print("=" * 78)
    print(f"Overall Severity Accuracy: {correct}/{total} = {accuracy:.1%}")
    print(f"Overall Script Integrity:  {script_passes}/{total} = {script_rate:.1%}")
    print(f"Combined RED-case recall:  {all_red_correct}/{len(all_red)} = {all_red_recall:.1%}")
    print("-" * 78)
    print(f"👉 English RED-case recall:     {en_red_correct}/{len(en_red)} = {en_red_recall:.1%}")
    print(f"👉 Non-English RED-case recall: {non_en_red_correct}/{len(non_en_red)} = {non_en_red_recall:.1%}")
    print("-" * 78)

    # Report script failures if any
    script_failures_found = False
    for lang, st in lang_stats.items():
        if st["script_failures"]:
            if not script_failures_found:
                print("\n⚠ DETECTED SCRIPT CORRUPTIONS / FAILURES:")
                script_failures_found = True
            for sym, reason in st["script_failures"]:
                print(f"  - [{lang}] {reason} on symptom: {sym}...")

    if not script_failures_found:
        print("\n✅ Zero script corruption issues detected across all evaluated cases!")

    if red_false_negatives:
        print("\n⚠ RED cases misclassified as non-RED (CRITICAL SAFETY ISSUES):")
        for r in red_false_negatives:
            print(f"  - [{r['language']}] expected RED, got {r['actual']}: {r['symptoms']}")
    else:
        print("\n✅ Zero RED false negatives! All emergency cases correctly identified.")

    print("\nConfusion matrix (expected -> actual counts):")
    for expected, actuals in confusion.items():
        print(f"  {expected}: {dict(actuals)}")
    print("=" * 78)

    return {
        "accuracy": accuracy,
        "script_rate": script_rate,
        "combined_red_recall": all_red_recall,
        "en_red_recall": en_red_recall,
        "non_en_red_recall": non_en_red_recall,
        "lang_stats": dict(lang_stats),
        "results": results
    }


if __name__ == "__main__":
    run_eval()
