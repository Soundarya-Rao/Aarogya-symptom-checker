"""
Thin wrapper around the Gemini API that adds:
  - structured (JSON-schema-validated) output for the symptom assessment
  - low-latency execution using gemini-3.5-flash-lite with minimal thinking mode
  - direct in-language assessment for Indian languages in a single round trip
  - retries with backoff for transient API failures
  - explicit user-facing exceptions (including RateLimitError)
"""

import os
import re
import time
import json
import logging
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from models import SymptomAssessment, SYMPTOM_ASSESSMENT_JSON_SCHEMA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("symptom_checker.llm_client")

# Load environment variables
load_dotenv(find_dotenv(usecwd=True))
_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key:
    # Fallback to direct path if needed
    alt_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(alt_env):
        load_dotenv(alt_env)
        _api_key = os.getenv("GEMINI_API_KEY")

if not _api_key:
    logger.warning(
        "GEMINI_API_KEY not found in environment. Make sure a .env file with "
        "GEMINI_API_KEY=your_key exists in the directory you're running from."
    )

client = genai.Client(api_key=_api_key)

# gemini-3.5-flash-lite provides highest throughput and lowest latency on free tier
MODEL_NAME = "gemini-3.5-flash-lite"
MAX_RETRIES = 3
BACKOFF_SECONDS = 2


class LLMError(Exception):
    """Raised when the model can't be reached or returns something unusable."""
    pass


class RateLimitError(LLMError):
    """Raised when rate limit (429 / RESOURCE_EXHAUSTED) is encountered."""
    def __init__(self, message: str, retry_delay: Optional[float] = None):
        super().__init__(message)
        self.retry_delay = retry_delay


class ScriptMismatchError(ValueError):
    """Raised when the LLM output is in an incorrect, mixed, or corrupted script."""
    pass


# Unicode script blocks for supported languages
UNICODE_SCRIPT_RANGES = {
    "Hindi": (0x0900, 0x097F),       # Devanagari
    "Marathi": (0x0900, 0x097F),     # Devanagari
    "Bengali": (0x0980, 0x09FF),     # Bengali
    "Tamil": (0x0B80, 0x0BFF),       # Tamil
    "Telugu": (0x0C00, 0x0C7F),      # Telugu
    "Kannada": (0x0C80, 0x0CFF),     # Kannada
    "Malayalam": (0x0D00, 0x0D7F),   # Malayalam
}

# Known foreign scripts that should NEVER appear in Indian language triage output
# (e.g. Armenian, Cyrillic, Greek, Georgian, Arabic, Hebrew)
FOREIGN_SCRIPT_RANGES = [
    (0x0530, 0x058F),  # Armenian
    (0x0400, 0x04FF),  # Cyrillic
    (0x0370, 0x03FF),  # Greek
    (0x10A0, 0x10FF),  # Georgian
    (0x0590, 0x05FF),  # Hebrew
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


def _validate_language_script(data: dict, language_name: str) -> None:
    """
    Defensive verification: ensure assessment text (what_to_do, possible_conditions)
    is actually rendered in a script consistent with the requested language.
    Raises ScriptMismatchError if foreign or corrupted scripts are detected.
    """
    lang = language_name.strip()
    if lang.lower() in ("english", "en"):
        # English text should not contain Indic or foreign script characters in what_to_do
        what_to_do = data.get("what_to_do", "")
        for ch in what_to_do:
            cp = ord(ch)
            if any(s <= cp <= e for s, e in ALL_INDIC_RANGES + FOREIGN_SCRIPT_RANGES):
                raise ScriptMismatchError(f"English assessment contains non-Latin character: U+{cp:04X} ({ch})")
        return

    expected_range = UNICODE_SCRIPT_RANGES.get(lang)
    if not expected_range:
        return

    s_exp, e_exp = expected_range
    what_to_do = data.get("what_to_do", "")
    conditions = data.get("possible_conditions", [])
    first_aid = data.get("first_aid_steps", [])

    # 1. Expected script presence in what_to_do (must have at least 5 chars of expected script)
    exp_count = sum(1 for ch in what_to_do if s_exp <= ord(ch) <= e_exp)
    if exp_count < 5:
        raise ScriptMismatchError(
            f"Expected {lang} script missing or insufficient in what_to_do (found {exp_count} characters)"
        )

    # 2. Check for explicitly corrupted / hallucinated foreign scripts (e.g. Armenian, Cyrillic)
    full_text = what_to_do + " " + " ".join(conditions) + " " + " ".join(first_aid)
    for ch in full_text:
        cp = ord(ch)
        for f_start, f_end in FOREIGN_SCRIPT_RANGES:
            if f_start <= cp <= f_end:
                raise ScriptMismatchError(
                    f"Corrupted foreign script detected in {lang} output: character U+{cp:04X} ({ch})"
                )

    # 3. Check for severe Indic script confusion in what_to_do (e.g. Devanagari in Kannada text)
    other_indic_ranges = [r for r in ALL_INDIC_RANGES if r != expected_range]
    other_indic_count = sum(1 for ch in what_to_do if any(s <= ord(ch) <= e for s, e in other_indic_ranges))
    if other_indic_count > 3:
        raise ScriptMismatchError(
            f"Mismatched Indic script characters detected in {lang} what_to_do (found {other_indic_count} mismatched characters)"
        )


def _extract_retry_delay(error: Exception) -> Optional[float]:
    """
    On a 429, Gemini's error includes the server's own suggested wait time
    (e.g. `retry_delay { seconds: 39 }` or `Please retry in 57s`).
    Retrying on a fixed 2s/4s/6s backoff against a quota that resets in 57s
    burns attempts for nothing, so we parse the real number out and honor it.
    """
    err_str = str(error)
    match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_str)
    if match:
        return float(match.group(1)) + 1
    match_sec = re.search(r"Please retry (?:after|in) (\d+)\.?\d*s", err_str, re.IGNORECASE)
    if match_sec:
        return float(match_sec.group(1)) + 1
    match_delay = re.search(r"['\"]?retryDelay['\"]?:\s*['\"]?(\d+)", err_str)
    if match_delay:
        return float(match_delay.group(1)) + 1
    return None


def _is_rate_limit(error: Exception) -> bool:
    err_str = str(error).lower()
    return "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str


def _call_model(prompt: str, response_mime_type: Optional[str] = None,
                 response_schema: Optional[dict] = None) -> str:
    config_params = {
        "thinking_config": types.ThinkingConfig(thinking_level="minimal"),
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
    }
    if response_mime_type:
        config_params["response_mime_type"] = response_mime_type
    if response_schema:
        config_params["response_schema"] = response_schema

    config = types.GenerateContentConfig(**config_params)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        start = time.time()
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=config,
            )
            elapsed = time.time() - start
            logger.info("Gemini call succeeded in %.2fs (attempt %d)", elapsed, attempt)
            if not response.text or not response.text.strip():
                raise LLMError("Model returned an empty response")
            return response.text
        except Exception as e:
            elapsed = time.time() - start
            last_error = e
            is_rate_limit = _is_rate_limit(e)
            server_delay = _extract_retry_delay(e)

            logger.warning(
                "LLM call failed after %.2fs (attempt %d/%d): %s",
                elapsed, attempt, MAX_RETRIES, e
            )

            if attempt < MAX_RETRIES:
                wait = server_delay if server_delay is not None else BACKOFF_SECONDS * attempt
                if server_delay is not None:
                    logger.info("Rate-limited by server; honoring suggested wait of %.0fs", wait)
                time.sleep(wait)
            else:
                if is_rate_limit:
                    raise RateLimitError(
                        f"Gemini API rate limit exceeded: {e}",
                        retry_delay=server_delay
                    ) from e

    raise LLMError(f"Model call failed after {MAX_RETRIES} attempts: {last_error}") from last_error


def translate_text(text: str, target_language_name: str) -> str:
    """Translate free text to the target language. Raises LLMError on failure."""
    start = time.time()
    prompt = (
        f"Translate this text to {target_language_name}. "
        f"Return only the translated text, nothing else:\n\n{text}"
    )
    try:
        result = _call_model(prompt).strip()
        logger.info("translate_text total: %.2fs", time.time() - start)
        return result
    except LLMError:
        logger.error("Translation failed for target language: %s", target_language_name)
        raise


def assess_symptoms(symptoms: str, state: str, language_name: str = "English") -> SymptomAssessment:
    """
    Get a structured, schema-validated assessment of symptoms.
    Supports assessing directly in English or any of the 8 Indian languages
    in a single round trip, and returns symptoms_in_english for logging.
    """
    start = time.time()
    is_english = language_name.strip().lower() in ("english", "en")

    if is_english:
        lang_instruction = (
            "Provide possible_conditions, what_to_do, and first_aid_steps in English.\n"
            "Keep symptoms_in_english as the original symptoms entered by the user."
        )
    else:
        native_script_hint = {
            "Hindi": "हिंदी (Devanagari script)",
            "Kannada": "ಕನ್ನಡ (Kannada script)",
            "Tamil": "தமிழ் (Tamil script)",
            "Telugu": "తెలుగు (Telugu script)",
            "Malayalam": "മലയാളം (Malayalam script)",
            "Marathi": "मराठी (Devanagari script)",
            "Bengali": "বাংলা (Bengali script)",
        }.get(language_name, language_name)
        lang_instruction = (
            f"The user is speaking {language_name}.\n"
            f"Provide possible_conditions, what_to_do, and first_aid_steps strictly in {native_script_hint}.\n"
            f"Do NOT use Armenian, Cyrillic, Latin transliteration, or any foreign script for the {language_name} sections.\n"
            "Provide symptoms_in_english as an accurate, concise English translation of the user's symptoms.\n"
            "Keep severity strictly as 'GREEN', 'YELLOW', or 'RED'."
        )

    prompt = f"""
You are a careful medical assistant helping people in {state}, India understand their symptoms.
{lang_instruction}

Respond ONLY with JSON matching this exact schema (no markdown fences, no extra text):
{json.dumps(SYMPTOM_ASSESSMENT_JSON_SCHEMA)}

User-described symptoms: {symptoms}

Rules you must follow:
- severity is "RED" only for clearly life-threatening symptoms (chest pain, stroke signs,
  difficulty breathing, unconsciousness, severe bleeding, poisoning)
- severity is "YELLOW" for symptoms needing a doctor within 24 hours
- severity is "GREEN" for mild symptoms manageable at home
- possible_conditions must be realistic and grounded in the symptoms described; if symptoms
  are too vague, say so honestly rather than guessing
- what_to_do should be practical advice for someone in {state}, India
- first_aid_steps must be non-empty numbered steps if emergency is true, otherwise an empty list
- Use simple language a 60 year old can understand
"""

    raw = _call_model(
        prompt,
        response_mime_type="application/json",
        response_schema=SYMPTOM_ASSESSMENT_JSON_SCHEMA,
    )

    try:
        data = json.loads(raw)
        if not data.get("symptoms_in_english"):
            data["symptoms_in_english"] = symptoms
        _validate_language_script(data, language_name)
        result = SymptomAssessment(**data)
        logger.info("assess_symptoms total: %.2fs (no retry needed)", time.time() - start)
        return result
    except (json.JSONDecodeError, ValidationError, ScriptMismatchError) as e:
        logger.error("Model output failed validation: %s | raw=%s", e, raw[:500])
        # One retry with an explicit correction nudge before giving up
        retry_prompt = prompt + (
            f"\n\nCRITICAL CORRECTION REQUIRED: Your previous response failed validation ({e}). "
            f"Ensure the JSON is strictly valid and that possible_conditions, what_to_do, and "
            f"first_aid_steps are written strictly in the {language_name} script, never in Armenian, Latin, "
            f"or any other language's script. Return ONLY valid JSON matching the schema exactly."
        )
        raw_retry = _call_model(
            retry_prompt,
            response_mime_type="application/json",
            response_schema=SYMPTOM_ASSESSMENT_JSON_SCHEMA,
        )
        try:
            data = json.loads(raw_retry)
            if not data.get("symptoms_in_english"):
                data["symptoms_in_english"] = symptoms
            _validate_language_script(data, language_name)
            result = SymptomAssessment(**data)
            logger.info("assess_symptoms total: %.2fs (needed 1 retry)", time.time() - start)
            return result
        except (json.JSONDecodeError, ValidationError, ScriptMismatchError) as e2:
            raise ValueError(f"Model output failed validation twice: {e2}") from e2
