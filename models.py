from pydantic import BaseModel, Field
from typing import Literal, List


class SymptomAssessment(BaseModel):
    """
    Structured output contract for the LLM's symptom assessment.

    Why this exists: the original version parsed the model's free text with
    `"SEVERITY: RED" in text`, which silently breaks the moment the model's
    formatting drifts even slightly. Requesting and validating JSON against
    this schema means a malformed response fails loudly (and can be retried)
    instead of quietly mis-routing a RED case as GREEN.
    """
    severity: Literal["GREEN", "YELLOW", "RED"]
    possible_conditions: List[str] = Field(
        description="2-3 medically plausible conditions, or a note that symptoms are too vague"
    )
    what_to_do: str
    emergency: bool
    first_aid_steps: List[str] = Field(
        default_factory=list,
        description="Numbered first-aid steps if emergency is True, otherwise empty"
    )
    symptoms_in_english: str = Field(
        default="",
        description="Concise English translation of the user's symptoms if entered in another language, or the original symptoms if English"
    )


# Gemini's `response_schema` only accepts a small subset of OpenAPI/JSON
# Schema (type, properties, items, enum, required, description -- no
# `additionalProperties`, `title`, `$defs`, etc). Pydantic's
# `model_json_schema()` includes those unsupported fields and gets rejected
# by the API with "Unknown field for Schema: additionalProperties", so this
# schema is written by hand to match exactly what Gemini accepts. The
# Pydantic model above is still what actually validates the parsed response.
SYMPTOM_ASSESSMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "severity": {
            "type": "string",
            "enum": ["GREEN", "YELLOW", "RED"],
        },
        "possible_conditions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-3 medically plausible conditions, or a note that symptoms are too vague",
        },
        "what_to_do": {"type": "string"},
        "emergency": {"type": "boolean"},
        "first_aid_steps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Numbered first-aid steps if emergency is true, otherwise an empty list",
        },
        "symptoms_in_english": {
            "type": "string",
            "description": "Concise English translation of the symptoms if entered in another language, or the symptoms as stated if in English",
        },
    },
    "required": ["severity", "possible_conditions", "what_to_do", "emergency", "first_aid_steps", "symptoms_in_english"],
}
