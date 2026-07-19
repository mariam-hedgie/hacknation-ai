"""Authenticated FastAPI façade and production host for the React frontend.

Planning stays framework-independent. Durable writes resolve Databricks proxy
identity on the server and use owner-scoped Lakebase persistence; the browser
can never choose an owner ID. In explicit local-demo mode, saved decisions are
process-local and reported as such.
"""

from __future__ import annotations

import sys
import base64
import binascii
import re
import secrets
from dataclasses import asdict
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.auth import AuthenticationError, AuthConfigurationError
from src.backend import service as backend
from src.backend.lakebase import plan_store_for_headers
from src.demo_adapter import CARE_TASKS
from src.journey import demo_journey_estimate, external_ticket_links, google_maps_directions_url
from src.localization import SUPPORTED_LANGUAGES
from src.nlp import configured_nlp_client, structure_intake
from src.ui_contract import AvenUiBackend
from src.voice import configured_voice_client, transcribe_for_review
from src.web_evidence import search_public_sources

app = FastAPI(title="Aven API")
DIST_DIR = APP_DIR / "frontend" / "dist"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Opaque, server-issued browser session. Used only to keep local-demo visitors
# on a shared host from seeing each other's scratch plans; it is never an
# identity and grants no access to authenticated Databricks persistence.
_DEMO_SESSION_COOKIE = "aven_demo_session"
_DEMO_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


@app.middleware("http")
async def issue_demo_session(request: Request, call_next):
    supplied = request.cookies.get(_DEMO_SESSION_COOKIE, "")
    session_key = supplied if _DEMO_SESSION_PATTERN.fullmatch(supplied) else secrets.token_urlsafe(24)
    request.state.demo_session = session_key
    response = await call_next(request)
    if session_key != supplied:
        response.set_cookie(
            _DEMO_SESSION_COOKIE,
            session_key,
            max_age=60 * 60 * 12,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
    return response


def ui_backend() -> AvenUiBackend:
    """A fresh stateless planning façade.

    Saved decisions use the authenticated stores exposed by the dedicated
    ``/api/plans`` routes below, never this planning-only session mapping.
    """
    return AvenUiBackend({})


class PlanRequest(BaseModel):
    message: str | None = Field(default=None, max_length=4_000)
    care_task: str = Field(max_length=80)
    capability: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=500)
    urgency: str = Field(default="routine", max_length=40)
    travel_tolerance: str = Field(default="medium", max_length=40)
    budget_sensitivity: str = Field(default="high", max_length=40)
    facility_preference: str = Field(default="either", max_length=40)
    language: str | None = Field(default=None, max_length=20)
    medication_name: str | None = Field(default=None, max_length=200)
    has_current_prescription: bool | None = None
    has_clinician_order: bool | None = None
    emergency_warning_reported: bool = False
    max_distance_km: int | None = Field(default=None, ge=0, le=50_000)
    travel_modes: list[str] = Field(default_factory=list, max_length=9)
    travel_budget_rupees: int | None = Field(default=None, ge=0, le=100_000_000)
    care_budget_rupees: int | None = Field(default=None, ge=0, le=100_000_000)
    required_arrival_date: str | None = Field(default=None, max_length=40)


@app.get("/api/languages")
def languages() -> dict[str, str]:
    return SUPPORTED_LANGUAGES


@app.get("/api/care-tasks")
def care_tasks() -> dict[str, str]:
    return CARE_TASKS


@app.get("/api/copy")
def copy(key: str, language: str = "en") -> dict[str, Any]:
    try:
        return ui_backend().copy(key, language)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/service-status")
def service_status() -> dict[str, Any]:
    status = ui_backend().service_status()
    status["backend_mode"] = backend.backend_mode()
    status["tools"] = backend.status()
    return status


@app.get("/api/travel-capabilities")
def travel_capabilities(modes: str = Query("walk,bus,train,car,taxi")) -> list[dict[str, Any]]:
    mode_list = [m.strip() for m in modes.split(",") if m.strip()]
    return list(ui_backend().travel_capabilities(mode_list))


@app.post("/api/plan")
def plan(request: PlanRequest) -> dict[str, Any]:
    """Run the domain safety gates, then plan. Mirrors app.py's
    show_confirmation(): only PROCEED carries options; every other branch is a
    blocking outcome the UI must render instead of a facility list."""
    response = ui_backend().confirm_and_plan(request.model_dump())
    return {
        "safety_branch": response.safety_branch,
        "options": list(response.options),
        "message": response.message,
        "validation_errors": list(response.validation_errors),
    }


class StructureIntakeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4_000)


@app.post("/api/structure-intake")
def structure_intake_request(request: StructureIntakeRequest) -> dict[str, Any]:
    """Return a review-only form draft. It never starts planning."""
    try:
        draft = structure_intake(request.text, client=configured_nlp_client())
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Automatic structuring is unavailable. Review the request manually.",
        ) from exc
    return asdict(draft)


class TranscribeRequest(BaseModel):
    # 10 MiB of audio expands to about 13.4 MiB as base64. Bound the encoded
    # request before decoding so an oversized body cannot amplify memory use.
    audio_base64: str = Field(max_length=14_000_000)
    language_code: str | None = Field(default=None, max_length=20)


@app.post("/api/transcribe")
def transcribe(request: TranscribeRequest) -> dict[str, Any]:
    try:
        audio = base64.b64decode(request.audio_base64, validate=True)
        transcript = transcribe_for_review(
            audio,
            client=configured_voice_client(),
            language_code=request.language_code,
        )
    except (ValueError, RuntimeError, binascii.Error) as exc:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription is unavailable. Continue with typed intake.",
        ) from exc
    return asdict(transcript)


class JourneyRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=500)
    destination: str = Field(min_length=1, max_length=500)
    mode: str = Field(min_length=1, max_length=30)
    distance_km: float | None = Field(default=None, ge=0, le=50_000)


@app.post("/api/journey")
def journey(request: JourneyRequest) -> dict[str, Any]:
    try:
        estimate = (
            asdict(demo_journey_estimate(request.distance_km, request.mode))
            if request.distance_km is not None and request.mode != "plane"
            else None
        )
        return {
            "maps_url": google_maps_directions_url(request.origin, request.destination, request.mode),
            "estimate": estimate,
            "ticket_links": [asdict(link) for link in external_ticket_links(request.mode)],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class PublicSourcesRequest(BaseModel):
    facility: str = Field(min_length=1, max_length=300)
    capability: str = Field(min_length=1, max_length=200)


@app.post("/api/public-sources")
def public_sources(request: PublicSourcesRequest) -> dict[str, Any]:
    """Return candidates for human verification, never ranking evidence."""
    try:
        candidates = search_public_sources(request.facility, request.capability)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Public-source lookup is unavailable. Verify through the facility directly.",
        ) from exc
    return {"candidates": [asdict(candidate) for candidate in candidates]}


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1_000)
    conversation_id: str | None = Field(default=None, max_length=128)


@app.post("/api/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    result = backend.ask_data_question(request.question, conversation_id=request.conversation_id)
    if result is None:
        return {"answered": False, "result": None}
    return {"answered": True, "result": result}


class SavedPlanRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    selected_facility_id: str | None = Field(default=None, max_length=256)
    selected_option: dict[str, Any]
    next_steps: list[str] = Field(default_factory=list, max_length=10)
    user_override: dict[str, Any] | None = None


class FeedbackRequest(BaseModel):
    status: str = Field(min_length=1, max_length=40)
    note: str = Field(default="", max_length=500)


def _request_store(request: Request):
    try:
        return plan_store_for_headers(
            dict(request.headers),
            session_key=getattr(request.state, "demo_session", ""),
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Sign in through Databricks to use saved plans.") from exc
    except (AuthConfigurationError, RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Saved plans are unavailable because secure persistence is not configured.") from exc


@app.get("/api/plans")
def list_plans(request: Request) -> dict[str, Any]:
    identity, store = _request_store(request)
    return {
        "persistence": "lakebase" if identity.authenticated else "local_demo",
        "plans": list(store.list_plans()),
    }


@app.get("/api/session")
def session(request: Request) -> dict[str, Any]:
    identity, _ = _request_store(request)
    return {
        "display_name": identity.display_name,
        "authenticated": identity.authenticated,
        "persistence": "lakebase" if identity.authenticated else "local_demo",
    }


@app.post("/api/plans")
def save_plan(request: Request, body: SavedPlanRequest) -> dict[str, Any]:
    identity, store = _request_store(request)
    try:
        saved = store.save_plan(body.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="The saved plan contains an invalid field.") from exc
    return {
        "persistence": "lakebase" if identity.authenticated else "local_demo",
        "plan": saved,
    }


@app.post("/api/plans/{plan_id}/feedback")
def save_plan_feedback(plan_id: str, request: Request, body: FeedbackRequest) -> dict[str, Any]:
    _, store = _request_store(request)
    try:
        return {"feedback": store.save_feedback(plan_id, body.model_dump())}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Saved plan not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Choose a supported feedback status and a shorter note.") from exc


@app.delete("/api/plans/{plan_id}")
def delete_plan(plan_id: str, request: Request) -> dict[str, bool]:
    _, store = _request_store(request)
    try:
        return {"deleted": store.delete_plan(plan_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid saved plan identifier.") from exc


if (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="react-assets")


@app.get("/{full_path:path}", include_in_schema=False)
def react_frontend(full_path: str):
    """Serve the built React SPA after Databricks runs the npm build step."""

    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found.")
    candidate = (DIST_DIR / full_path).resolve()
    if DIST_DIR.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    index = DIST_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=503, detail="React build is not available.")
