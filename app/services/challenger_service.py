import json
import time

from google import genai
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.claim import Claim
from app.models.claim_relationship import ClaimRelationship
from app.models.challenge_output import ChallengeOutput, ChallengeOutputClaim
from app.schemas.challenge_output import ChallengeCategory


_client = genai.Client(api_key=settings.LLM_API_KEY)

_VALID_CATEGORIES = set(c.value for c in ChallengeCategory)

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 3

_SYSTEM_INSTRUCTION = (
    "You are the Challenger inside CapitalOS, a structured investment "
    "reasoning tool. Your ONLY job is to critique the reasoning you are "
    "given, in exactly these five categories: "
    "missing_evidence (a claim asserts something without adequate "
    "supporting evidence), unstated_assumption (a claim depends on a "
    "condition that is never stated or justified), contradiction (two "
    "claims conflict with each other), alternative_explanation (a "
    "plausible alternative reading of the evidence exists), and "
    "invalidation_condition (a concrete, checkable condition that would "
    "prove the reasoning wrong). "
    "STRICT RULES: You must NEVER recommend a decision, action, or trade "
    "such as buy, sell, or avoid this investment. You must NEVER state "
    "your own view on whether the investment is good or bad. You only "
    "critique the structure and completeness of the reasoning given to "
    "you. Every challenge must reference at least one claim_id from the "
    "claims provided. Return ONLY valid JSON, with no extra text, in "
    "this exact shape: a JSON object with a key named challenges, whose "
    "value is a list of objects, each with a category field set to one "
    "of the five categories above, a text field containing the "
    "challenge phrased as an observation or question, and a claim_ids "
    "field containing a list of integer claim ids."
)


def _build_context(claims, relationships):
    claim_lines = []
    for c in claims:
        line = "- claim_id=" + str(c.id) + ": statement=" + str(c.statement)
        line = line + " temporal_orientation=" + str(c.temporal_orientation)
        line = line + " epistemic_role=" + str(c.epistemic_role)
        line = line + " shape=" + str(c.shape)
        line = line + " confidence_band=" + str(c.confidence_band)
        claim_lines.append(line)
    claims_block = chr(10).join(claim_lines)

    if relationships:
        rel_lines = []
        for r in relationships:
            rel_line = "- claim " + str(r.from_claim_id) + " "
            rel_line = rel_line + str(r.relationship_type) + " claim "
            rel_line = rel_line + str(r.to_claim_id)
            rel_lines.append(rel_line)
        relationships_block = chr(10).join(rel_lines)
    else:
        relationships_block = "(none)"

    result = "CLAIMS:" + chr(10) + claims_block + chr(10) + chr(10)
    result = result + "CLAIM RELATIONSHIPS:" + chr(10) + relationships_block
    result = result + chr(10) + chr(10)
    result = result + "Generate 1 to 3 structured challenges for this "
    result = result + "reasoning, following the rules and JSON shape exactly."
    return result


def _call_llm(claims, relationships):
    prompt = _build_context(claims, relationships)

    last_error = None
    response = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = _client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
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
        raise last_error

    parsed = json.loads(response.text)
    raw_challenges = parsed.get("challenges", [])

    valid_claim_ids = set(c.id for c in claims)
    validated = []
    for item in raw_challenges:
        category = item.get("category")
        text = item.get("text")
        claim_ids = item.get("claim_ids", [])

        if category not in _VALID_CATEGORIES:
            continue
        if not text:
            continue
        claim_ids = [cid for cid in claim_ids if cid in valid_claim_ids]
        if not claim_ids:
            continue

        validated.append({"category": category, "text": text, "claim_ids": claim_ids})

    return validated


def generate_challenges(db, case_id):
    claims = db.query(Claim).filter(Claim.research_case_id == case_id).all()

    if not claims:
        return []

    claim_ids_list = [c.id for c in claims]
    relationships = (
        db.query(ClaimRelationship)
        .filter(ClaimRelationship.from_claim_id.in_(claim_ids_list))
        .all()
    )

    validated_challenges = _call_llm(claims, relationships)

    results = []
    for item in validated_challenges:
        challenge = ChallengeOutput(
            research_case_id=case_id,
            category=item["category"],
            text=item["text"],
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)

        for claim_id in item["claim_ids"]:
            link = ChallengeOutputClaim(
                challenge_output_id=challenge.id, claim_id=claim_id
            )
            db.add(link)
        db.commit()

        results.append(challenge)

    return results


def list_challenges(db, case_id):
    return (
        db.query(ChallengeOutput)
        .filter(ChallengeOutput.research_case_id == case_id)
        .all()
    )


def get_claim_ids_for_challenge(db, challenge_id):
    links = (
        db.query(ChallengeOutputClaim)
        .filter(ChallengeOutputClaim.challenge_output_id == challenge_id)
        .all()
    )
    return [link.claim_id for link in links]