"""HTTP façade over Aven's existing Python core, for the React frontend.

This module adds no new product logic: every endpoint is a thin translation of
an existing, framework-independent function (src/ui_contract.py,
src/backend/service.py, src/profiles.py, src/demo_adapter.py). The Streamlit
app (app.py) keeps working unchanged and is still what app.yaml deploys — this
is an additional local API for the React UI in frontend/.

All endpoints are stateless per-request except profile persistence, which is
keyed by email exactly like src/profiles.py's local JSON store. There is no
server-side session: the React client owns its own draft/request/results state
and only calls out to Python for safety-gated planning, governed translations,
and file-backed profile storage.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src import profiles
from src.backend import service as backend
from src.demo_adapter import CARE_TASKS
from src.localization import SUPPORTED_LANGUAGES
from src.ui_contract import AvenUiBackend

app = FastAPI(title="Aven API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def ui_backend() -> AvenUiBackend:
    """A fresh, stateless façade instance. Only its plan-store methods need
    real session persistence, and neither the React app nor app.py's own flow
    uses those (app.py manages saved plans itself via src/profiles.py), so a
    throwaway dict is always sufficient here."""
    return AvenUiBackend({})


class PlanRequest(BaseModel):
    message: str | None = None
    care_task: str
    capability: str | None = None
    location: str | None = None
    urgency: str = "routine"
    travel_tolerance: str = "medium"
    budget_sensitivity: str = "high"
    facility_preference: str = "either"
    language: str | None = None
    medication_name: str | None = None
    has_current_prescription: bool | None = None
    has_clinician_order: bool | None = None
    emergency_warning_reported: bool = False


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


class AskRequest(BaseModel):
    question: str
    conversation_id: str | None = None


@app.post("/api/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    result = backend.ask_data_question(request.question, conversation_id=request.conversation_id)
    if result is None:
        return {"answered": False, "result": None}
    return {"answered": True, "result": result}


@app.get("/api/profile")
def get_profile(email: str = "") -> dict[str, Any]:
    return backend.load_profile(email) if email.strip() else profiles.empty_profile()


class ProfileRequest(BaseModel):
    profile: dict[str, Any]


@app.post("/api/profile")
def save_profile(request: ProfileRequest) -> dict[str, Any]:
    backend.save_profile(request.profile)
    return request.profile
