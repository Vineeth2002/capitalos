from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import (  # noqa: F401 - ensures tables are registered
    entity,
    research_case,
    claim,
    claim_relationship,
    challenge_output,
)
from app.api import (
    entities,
    research_cases,
    claims,
    claim_relationships,
    challenges,
    reasoning_intake,
)

app = FastAPI(title=settings.APP_NAME)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(entities.router)
app.include_router(research_cases.router)
app.include_router(claims.router)
app.include_router(claim_relationships.router)
app.include_router(challenges.router)
app.include_router(reasoning_intake.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/cases", response_class=HTMLResponse)
def cases_list(request: Request):
    return templates.TemplateResponse(request, "cases.html", {})


@app.get("/cases/{case_id}", response_class=HTMLResponse)
def case_workspace(request: Request, case_id: int):
    return templates.TemplateResponse(
        request, "workspace.html", {"case_id": case_id}
    )


@app.get("/health")
def health():
    return {"status": "ok"}