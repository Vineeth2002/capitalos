from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.rate_limiter import enforce_intake_rate_limit
from app.db.session import get_db
from app.schemas.reasoning_intake import (
    ReasoningIntakeRequest,
    ReasoningIntakeResponse,
)
from app.schemas.reasoning_intake_confirm import (
    ReasoningIntakeConfirmRequest,
    ReasoningIntakeConfirmResponse,
)
from app.services import reasoning_intake_service
from app.services import reasoning_intake_confirm_service
from app.services.reasoning_intake_service import IntakeUnavailableError

router = APIRouter(tags=["reasoning-intake"])


@router.post(
    "/reasoning-intake",
    response_model=ReasoningIntakeResponse,
    dependencies=[Depends(enforce_intake_rate_limit)],
)
def create_reasoning_intake(payload: ReasoningIntakeRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")

    try:
        result = reasoning_intake_service.extract_reasoning(payload.text)
    except IntakeUnavailableError:
        raise HTTPException(
            status_code=503,
            detail=(
                "The reasoning intake AI provider is temporarily "
                "unavailable. Please try again in a few minutes."
            ),
        )

    return result


@router.post(
    "/reasoning-intake/confirm",
    response_model=ReasoningIntakeConfirmResponse,
)
def confirm_reasoning_intake(
    payload: ReasoningIntakeConfirmRequest, db: Session = Depends(get_db)
):
    if not payload.claims:
        raise HTTPException(
            status_code=422, detail="At least one claim is required"
        )

    try:
        research_case, claims = reasoning_intake_confirm_service.confirm_reasoning(
            db, payload
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))

    return ReasoningIntakeConfirmResponse(
        research_case=research_case, claims=claims
    )