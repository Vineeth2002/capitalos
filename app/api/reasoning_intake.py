from fastapi import APIRouter, Depends, HTTPException

from app.core.rate_limiter import enforce_intake_rate_limit
from app.schemas.reasoning_intake import (
    ReasoningIntakeRequest,
    ReasoningIntakeResponse,
)
from app.services import reasoning_intake_service
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