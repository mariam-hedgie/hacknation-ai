"""Deterministic local data adapter for the Aven UI demo.

This module contains no challenge data and makes no medical, availability, or
pricing claims. Replace this adapter with a Databricks-backed implementation
that returns the same option shape once the platform tables are ready.
"""

from __future__ import annotations

from typing import Any

from .enrichment import normalize


CARE_TASKS = {
    "known_referral": "Referral, specialty, or procedure",
    "refill": "Medication refill or pharmacy",
    "lab": "Lab test or blood draw",
    "vaccination": "Vaccination or immunization",
    "symptom_first": "I am not sure what care I need",
    "follow_up": "Follow-up or appointment question",
}


TASK_QUESTIONS = {
    "known_referral": "What specialty, procedure, or care need did your doctor write down?",
    "refill": "What medicine and formulation do you need refilled?",
    "lab": "What test or blood draw did your clinician request?",
    "vaccination": "Which vaccine or immunization are you planning for?",
    "symptom_first": "What is worrying you today? We can help plan a possible next care step, not diagnose it.",
    "follow_up": "Which facility or doctor are you trying to reach?",
}


def infer_care_task(message: str) -> str:
    """Return a conservative care task inferred from common, non-clinical words."""
    text = (message or "").lower()
    if any(term in text for term in ("refill", "prescription", "medicine", "medication", "pharmacy")):
        return "refill"
    if any(term in text for term in ("blood draw", "blood test", "lab", "test order", "diagnostic test")):
        return "lab"
    if any(term in text for term in ("appointment", "follow-up", "follow up", "doctor told", "referral", "specialist", "procedure")):
        return "follow_up" if "appointment" in text or "follow" in text else "known_referral"
    return "symptom_first"


def next_question(care_task: str) -> str:
    """Return the next task-specific question, defaulting to the safe symptom flow."""
    return TASK_QUESTIONS.get(care_task, TASK_QUESTIONS["symptom_first"])


# Seeded payloads in the extractor's OUTPUT SCHEMA (see src/enrichment.py). The
# three deliberately cover the states the card must handle: a rich record, a
# sparse one (data desert), and one that is both conflicting and possibly two
# facilities merged into one row. All text is invented for the demo.
_DEMO_ENRICHMENT: list[dict[str, Any]] = [
    {
        "capabilities": [
            {"claim": "Outpatient cardiology consultation",
             "evidence": ["Demo record: “daily outpatient cardiology OPD, 9am–1pm”"]},
            {"claim": "24-hour emergency intake",
             "evidence": ["Demo record: “casualty department open 24 hours”"]},
        ],
        "procedures": [
            {"claim": "ECG", "evidence": ["Demo record: “ECG performed on site”"]},
            {"claim": "Treadmill stress test", "evidence": []},
        ],
        "equipment": [
            {"claim": "Colour doppler echocardiography unit",
             "evidence": ["Demo record: “2D echo with colour doppler installed 2019”"]},
        ],
        "specialties": ["Cardiology", "General medicine"],
        "facility_facts": [
            {"fact": "Wheelchair-accessible entrance",
             "evidence": ["Demo record: “ramp access at main entrance”"]},
        ],
        "data_quality": {
            "has_rich_description": True,
            "conflicting_claims": [],
            "possible_merged_facility": False,
            "merge_suspicion_reason": None,
        },
    },
    {
        "capabilities": [{"claim": "General outpatient consultation", "evidence": []}],
        "procedures": [],
        "equipment": [],
        "specialties": ["General medicine"],
        "facility_facts": [],
        "data_quality": {
            "has_rich_description": False,
            "conflicting_claims": [],
            "possible_merged_facility": False,
            "merge_suspicion_reason": None,
        },
    },
    {
        "capabilities": [
            {"claim": "Specialty outpatient clinic",
             "evidence": ["Demo record: “specialist clinics run on weekdays”"]},
        ],
        "procedures": [{"claim": "Diagnostic imaging", "evidence": ["Demo record: “X-ray and ultrasound”"]}],
        "equipment": [],
        "specialties": ["Cardiology", "Radiology"],
        "facility_facts": [],
        "data_quality": {
            "has_rich_description": True,
            "conflicting_claims": [
                "One record lists a 24-hour pharmacy; another lists pharmacy hours as 9am–6pm.",
                "Bed count appears as both 40 and 120 across records.",
            ],
            "possible_merged_facility": True,
            "merge_suspicion_reason": "Two distinct addresses and phone numbers appear under one facility name.",
        },
    },
]


def build_demo_options(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Produce stable, clearly seeded options for UI development and rehearsal.

    Future data adapters must return this same display contract but replace all
    seeded content with literal source-backed evidence and real status labels.
    """
    capability = str(request.get("capability") or "the confirmed care need")
    preference = str(request.get("facility_preference") or "either")
    public_note = "A public-facility preference was included in this demo ranking." if preference == "public" else "Your selected preferences were included in this demo ranking."

    options: list[dict[str, Any]] = [
        {
            "label": "Best documented fit",
            "facility": "Demo District Care Centre",
            "summary": f"A seeded demonstration option for {capability}.",
            "travel": "Travel estimate: demo estimate — confirm your route before leaving.",
            "cost": "Consultation price: not confirmed — call before leaving.",
            "evidence": "Demo evidence receipt: a future Databricks record will show the literal supporting facility text here.",
            "unknowns": "We could not confirm real-time service availability, appointment slots, or consultation price.",
            "next_step": "Call the official facility contact once it is sourced, then ask whether the needed service is currently available.",
            "ranking": f"Chosen because it is the strongest seeded evidence match. {public_note}",
        },
        {
            "label": "Lower-burden route",
            "facility": "Demo Community Hospital",
            "summary": f"A seeded demo lower-travel alternative for {capability}.",
            "travel": "Travel estimate: demo estimate — this is not live transit information.",
            "cost": "Cost: not confirmed — public status does not guarantee affordability or eligibility.",
            "evidence": "Demo evidence receipt: the production adapter will cite a literal facility-data span.",
            "unknowns": "We could not confirm the fee, scheme eligibility, or current capacity.",
            "next_step": "Call first and ask about the care need, referral requirements, and expected charges.",
            "ranking": "Chosen as a seeded lower-burden alternative, not as a claim of lower clinical quality or cost.",
        },
        {
            "label": "Alternative to verify",
            "facility": "Demo Specialty Centre",
            "summary": f"A seeded demo alternative that may fit {capability} but needs verification.",
            "travel": "Travel estimate: demo estimate — confirm transport and travel time before planning.",
            "cost": "Consultation price: not confirmed.",
            "evidence": "Demo evidence receipt: the production adapter will display supporting and conflicting source text when present.",
            "unknowns": "We could not confirm this option's current service, cost, appointment, or accessibility details.",
            "next_step": "Use the future official contact link or call script to confirm details before travel.",
            "ranking": "Included to make uncertainty visible and preserve a user choice beyond the first recommendation.",
        },
    ]
    for option, payload in zip(options, _DEMO_ENRICHMENT):
        option["enrichment"] = normalize(payload)
    return options
