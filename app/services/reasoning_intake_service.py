import json
import time

from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings


class IntakeUnavailableError(Exception):
    # Raised when the LLM provider remains unavailable after all retry
    # attempts are exhausted. Generic and provider-agnostic, same pattern
    # as ChallengerUnavailableError in challenger_service.py.
    pass


_client = genai.Client(api_key=settings.LLM_API_KEY)

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 3

_VALID_TEMPORAL = set(["historical", "current", "forecast"])
_VALID_EPISTEMIC = set(
    ["evidence", "interpretation", "assumption", "risk", "hypothesis"]
)
_VALID_SHAPE = set(["quantitative", "qualitative"])

_DEFAULT_NEEDS_MORE_MESSAGE = (
    "I couldn't identify enough of your own reasoning to extract grounded "
    "claims. Describe what you currently think, why you think it, and "
    "what you're uncertain about."
)

_SYSTEM_INSTRUCTION = (
    "You help structure a person's natural-language reasoning about a real "
    "decision into a draft form for a reasoning tool called CapitalOS. You "
    "do NOT decide anything and you do NOT give advice. You only extract "
    "structure from what the person actually wrote. "
    ""
    "CRITICAL GROUNDING RULE: you must NEVER invent, guess, or generate "
    "plausible-sounding beliefs just because a topic, name, or keyword "
    "appears in the input. Your only source of truth is the literal "
    "content the person wrote. If the input is an instruction to you "
    "rather than a person's own reasoning (for example, a placeholder, an "
    "example prompt, a meta-request telling you what to extract, or text "
    "that describes what SHOULD be written rather than actually containing "
    "someone's reasoning), you must NOT manufacture reasoning about the "
    "topic it mentions. In that case, set needs_more_reasoning to true, "
    "leave objective_context null, leave draft_claims and "
    "inferred_candidates as empty lists, and set message to a short, "
    "clear request for the person to describe what they actually think, "
    "why, and what they are uncertain about. The same applies if the "
    "input is too short or vague to support any grounded claim - return "
    "only what is directly supported by the text, and if that is nothing, "
    "say so rather than filling the gap with generic or invented content. "
    "Fabricating a plausible-sounding belief is a worse failure than "
    "returning nothing. "
    ""
    "When the input DOES contain a person's real reasoning, separate it "
    "into three parts. First, objective_context: a short summary (1-3 "
    "sentences) of what the person is trying to achieve or their stated "
    "goals/preferences - not a belief about the world, just their "
    "objective, in their own terms. Second, draft_claims: a list of "
    "atomic beliefs the person DIRECTLY stated, each with a statement, a "
    "temporal_orientation (historical, current, or forecast), an "
    "epistemic_role (evidence, interpretation, assumption, risk, or "
    "hypothesis), and a shape (quantitative or qualitative). Only include "
    "things the person actually said, phrased close to their own words. "
    "Third, inferred_candidates: things you suspect might be true based on "
    "the wording or tone, but which the person did NOT directly state - "
    "each with a statement and a reason. These are candidates only. "
    ""
    "Return ONLY valid JSON, no extra text, in this exact shape: an "
    "object with keys objective_context (string or null), draft_claims "
    "(array of objects with statement, temporal_orientation, "
    "epistemic_role, shape), inferred_candidates (array of objects with "
    "statement and reason), needs_more_reasoning (boolean), and message "
    "(string or null, only set when needs_more_reasoning is true)."
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
        except genai_errors.ClientError as exc:
            # Client errors (e.g. 429 quota exceeded) will not be fixed by
            # retrying within seconds, unlike transient ServerErrors. Fail
            # immediately rather than wasting retry attempts.
            last_error = exc
            break

    if last_error is not None:
        raise IntakeUnavailableError(
            "The reasoning intake AI provider was unavailable after "
            + str(_MAX_RETRIES)
            + " attempts."
        ) from last_error

    return json.loads(response.text)


def extract_reasoning(text):
    raw = _call_llm(text)

    needs_more_reasoning = bool(raw.get("needs_more_reasoning", False))

    if needs_more_reasoning:
        message = raw.get("message")
        if not message:
            message = _DEFAULT_NEEDS_MORE_MESSAGE
        return {
            "objective_context": None,
            "draft_claims": [],
            "inferred_candidates": [],
            "needs_more_reasoning": True,
            "message": message,
        }

    objective_context = raw.get("objective_context")
    if not isinstance(objective_context, str):
        objective_context = None

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
        "needs_more_reasoning": False,
        "message": None,
    }