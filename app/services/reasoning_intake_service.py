import json
import time

from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings


class IntakeUnavailableError(Exception):
    # Raised when the LLM provider remains unavailable after all retry
    # attempts are exhausted. Generic and provider-agnostic, same pattern
    # as ChallengerUnavailableError in challenger_service.py - the API
    # route layer never needs to know which provider failed.
    pass


_client = genai.Client(api_key=settings.LLM_API_KEY)

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 3

_VALID_TEMPORAL = set(["historical", "current", "forecast"])
_VALID_EPISTEMIC = set(
    ["evidence", "interpretation", "assumption", "risk", "hypothesis"]
)
_VALID_SHAPE = set(["quantitative", "qualitative"])

_SYSTEM_INSTRUCTION = (
    "You help structure a person's natural-language reasoning about a real "
    "decision into a draft form for a reasoning tool called CapitalOS. You "
    "do NOT decide anything and you do NOT give advice. You only extract "
    "structure from what the person actually wrote. "
    "Separate the input into three parts. "
    "First, objective_context: a short summary (1-3 sentences) of what the "
    "person is trying to achieve or their stated goals/preferences - not a "
    "belief about the world, just their objective, in their own terms. "
    "Second, draft_claims: a list of atomic beliefs the person DIRECTLY "
    "stated, each with a statement, a temporal_orientation (historical, "
    "current, or forecast), an epistemic_role (evidence, interpretation, "
    "assumption, risk, or hypothesis), and a shape (quantitative or "
    "qualitative). Only include things the person actually said, phrased "
    "close to their own words - do not invent beliefs they did not state. "
    "Third, inferred_candidates: things you suspect might be true based on "
    "the wording or tone, but which the person did NOT directly state - "
    "each with a statement and a reason explaining why you inferred it. "
    "These are candidates only and must be clearly separated from "
    "draft_claims, since the person must confirm them before they become "
    "real claims. Return ONLY valid JSON, no extra text, in this exact "
    "shape: an object with keys objective_context (string), draft_claims "
    "(array of objects with statement, temporal_orientation, "
    "epistemic_role, shape), and inferred_candidates (array of objects "
    "with statement and reason)."
)


def _call_llm(text):
    last_error = None
    response = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = _client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=text,
                config={
                    "system_instruction": _SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                },
            )
            last_error = None
            break
        except genai_errors.ServerError as exc:
            last_error = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_SECONDS * attempt)

    if last_error is not None:
        raise IntakeUnavailableError(
            "The reasoning intake AI provider was unavailable after "
            + str(_MAX_RETRIES)
            + " attempts."
        ) from last_error

    return json.loads(response.text)


def extract_reasoning(text):
    raw = _call_llm(text)

    objective_context = raw.get("objective_context", "")
    if not isinstance(objective_context, str):
        objective_context = ""

    cleaned_claims = []
    for item in raw.get("draft_claims", []):
        statement = item.get("statement")
        temporal_orientation = item.get("temporal_orientation")
        epistemic_role = item.get("epistemic_role")
        shape = item.get("shape")

        if not statement:
            continue
        if temporal_orientation not in _VALID_TEMPORAL:
            continue
        if epistemic_role not in _VALID_EPISTEMIC:
            continue
        if shape not in _VALID_SHAPE:
            continue

        cleaned_claims.append(
            {
                "statement": statement,
                "temporal_orientation": temporal_orientation,
                "epistemic_role": epistemic_role,
                "shape": shape,
            }
        )

    cleaned_candidates = []
    for item in raw.get("inferred_candidates", []):
        statement = item.get("statement")
        reason = item.get("reason")
        if not statement or not reason:
            continue
        cleaned_candidates.append({"statement": statement, "reason": reason})

    return {
        "objective_context": objective_context,
        "draft_claims": cleaned_claims,
        "inferred_candidates": cleaned_candidates,
    }