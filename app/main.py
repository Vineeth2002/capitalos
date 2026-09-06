from fastapi import FastAPI

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import entity, research_case, claim  # noqa: F401 - ensures tables are registered
from app.api import entities, research_cases, claims

app = FastAPI(title=settings.APP_NAME)

Base.metadata.create_all(bind=engine)

app.include_router(entities.router)
app.include_router(research_cases.router)
app.include_router(claims.router)


@app.get("/health")
def health():
    return {"status": "ok"}