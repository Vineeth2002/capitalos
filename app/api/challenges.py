from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rate_limiter import enforce_challenge_rate_limit
from app.db.session import get_db
from app.models.research_case import ResearchCase
from app.schemas.challenge_output import ChallengeOutputResponse
from app.services import challenger_service

router = APIRouter(tags=["challenges"])


def _to_response(db: Session, challenge) -> ChallengeOutputResponse:
    claim_ids = challenger_service.get_claim_ids_for_challenge(db, challenge.id)
    return ChallengeOutputResponse(
        id=challenge.id,
        research_case_id=challenge.research_case_id,
        category=challenge.category,
        text=challenge.text,
        claim_ids=claim_ids,
        created_at=challenge.created_at,
    )


@router.post(
    "/research-cases/{case_id}/challenge",
    response_model=list[ChallengeOutputResponse],
    dependencies=[Depends(enforce_challenge_rate_limit)],
)
def create_challenges(case_id: int, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")

    challenges = challenger_service.generate_challenges(db, case_id)
    return [_to_response(db, c) for c in challenges]


@router.get(
    "/research-cases/{case_id}/challenges",
    response_model=list[ChallengeOutputResponse],
)
def list_challenges(case_id: int, db: Session = Depends(get_db)):
    case = db.get(ResearchCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Research case not found")

    challenges = challenger_service.list_challenges(db, case_id)
    return [_to_response(db, c) for c in challenges]