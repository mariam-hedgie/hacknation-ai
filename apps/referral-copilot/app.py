"""Aven's Streamlit vertical slice with safe, deterministic fallbacks."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.app_logic import evaluate_demo_request
from src.databricks_adapter import SessionLocalPlanStore, load_databricks_config
from src.demo_adapter import CARE_TASKS, infer_care_task, next_question
from src.domain import SafetyBranch
from src.localization import (
    SUPPORTED_LANGUAGES,
    resolve_language,
    translate_core,
    voice_provider_status,
)
from src.maps import SUPPORTED_TRAVEL_MODES, mode_capability, select_map_provider


def initialize_state() -> None:
    defaults = {
        "stage": "intake",
        "selected_language": "en",
        "saved_plan_ids": [],
        "active_plan_id": None,
        "request": None,
        "outcome": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {max-width: 880px; padding-top: 3.5rem; padding-bottom: 4rem;}
        h1, h2, h3 {letter-spacing: -0.025em;}
        [data-testid="stMetric"] {background: #f6f8f7; border: 1px solid #dfe7e3; padding: .8rem; border-radius: .8rem;}
        [data-testid="stAlert"] {border-radius: .8rem;}
        .aven-kicker {color: #236b57; font-weight: 700; text-transform: uppercase; letter-spacing: .09em; font-size: .78rem;}
        .aven-step {color: #58645f; font-size: .9rem; margin-bottom: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_header() -> None:
    left, right = st.columns([3, 1])
    with left:
        st.markdown('<div class="aven-kicker">Care access planner</div>', unsafe_allow_html=True)
        st.title("Aven")
        st.caption("The right care route, with proof.")
    with right:
        language_codes = list(SUPPORTED_LANGUAGES)
        current = st.session_state.selected_language
        selected = st.selectbox(
            "Language",
            language_codes,
            index=language_codes.index(current),
            format_func=lambda code: SUPPORTED_LANGUAGES[code],
            key="language_selector",
        )
        st.session_state.selected_language = selected

    safety = translate_core("medical_safety_notice", st.session_state.selected_language)
    st.info(safety.text)
    st.markdown(
        '<div class="aven-step">1 Tell us &nbsp;→&nbsp; 2 Confirm &nbsp;→&nbsp; 3 Your plan</div>',
        unsafe_allow_html=True,
    )


def show_service_status() -> None:
    map_provider = select_map_provider()
    voice = voice_provider_status()
    try:
        databricks_ready = load_databricks_config() is not None
    except ValueError:
        databricks_ready = False

    with st.expander("Demo and connection status"):
        st.write(
            f"**Facility records:** {'Databricks identifiers detected' if databricks_ready else 'seeded demo adapter'}"
        )
        st.write(f"**Travel layer:** {map_provider.name} mode")
        st.write(f"**Voice:** {voice.public_message}")
        st.caption(
            "Seeded results are labelled as demo. A credential being detected does not prove that a live request succeeded."
        )


def show_emergency_stop() -> None:
    st.error("Get urgent help now")
    st.write(
        "Seek local emergency care now. Do not wait for a facility comparison. "
        "Aven will not rank ordinary options on this path."
    )
    if st.button("Start a new non-urgent request"):
        st.session_state.stage = "intake"
        st.rerun()


def show_intake() -> None:
    st.subheader(translate_core("tell_us", st.session_state.selected_language).text)
    st.write(
        "Describe the care-access problem in your own words. You will review every extracted detail before Aven creates a plan."
    )
    message = st.text_area(
        "Your request",
        placeholder="Example: My doctor wrote a cardiology referral. I am near Patna and need to keep travel and cost low.",
        max_chars=2_000,
        key="request_text",
    )
    inferred = infer_care_task(message)
    care_task = st.selectbox(
        "What kind of help do you need?",
        options=list(CARE_TASKS),
        index=list(CARE_TASKS).index(inferred),
        format_func=lambda value: CARE_TASKS[value],
    )

    emergency = False
    possible_setting = ""
    if care_task == "symptom_first":
        st.warning(
            "Aven cannot assess or diagnose symptoms. Answer the emergency check before ordinary planning."
        )
        emergency = st.checkbox(
            "I may have an emergency warning sign or need immediate help",
            key="emergency_check",
        )
        if emergency:
            show_emergency_stop()
            return

    with st.form("intake_form"):
        detail = st.text_input(
            "A little more detail", placeholder=next_question(care_task), key="care_detail"
        )
        if care_task == "symptom_first":
            possible_setting = st.selectbox(
                "Possible first care setting — please review",
                ["", "Primary care", "Urgent care"],
                format_func=lambda value: value or "Not yet confirmed",
                key="possible_care_setting",
            )

        has_prescription = None
        if care_task == "refill":
            has_prescription = st.checkbox(
                "I have a current prescription or refill instruction",
                key="has_current_prescription",
            )

        has_order = None
        if care_task == "lab":
            has_order = st.checkbox(
                "A clinician provided this test order or referral", key="has_clinician_order"
            )

        location = st.text_input(
            "Starting city, district, or pincode",
            placeholder="Patna, Bihar",
            key="starting_location",
        )
        urgency = st.select_slider(
            "How soon do you need to act?",
            options=["Routine", "Soon", "Urgent"],
            value="Soon",
            key="urgency_slider",
        )
        travel = st.select_slider(
            "How much travel can you manage?",
            options=["Low", "Medium", "High"],
            value="Medium",
            key="travel_slider",
        )
        budget = st.select_slider(
            "How important is minimizing cost?",
            options=["Low", "Medium", "High"],
            value="High",
            key="budget_slider",
        )
        preference = st.radio(
            "Facility preference",
            options=["Either", "Public", "Private"],
            horizontal=True,
            key="facility_preference",
        )
        modes = st.multiselect(
            "Travel modes to compare",
            SUPPORTED_TRAVEL_MODES,
            default=["car", "bus", "train"],
            key="travel_modes",
        )
        submitted = st.form_submit_button(
            "Review what Aven understood", type="primary", key="review_request"
        )

    if submitted:
        capability = possible_setting if care_task == "symptom_first" else detail
        st.session_state.request = {
            "original_message": message,
            "care_task": care_task,
            "capability": capability,
            "reported_need": detail or message,
            "medication_name": detail if care_task == "refill" else None,
            "has_current_prescription": has_prescription,
            "has_clinician_order": has_order,
            "location": location,
            "urgency": urgency.casefold(),
            "travel_tolerance": travel.casefold(),
            "budget_sensitivity": budget.casefold(),
            "facility_preference": preference.casefold(),
            "language": st.session_state.selected_language,
            "travel_modes": modes,
            "emergency_warning_reported": emergency,
        }
        st.session_state.stage = "confirm"
        st.rerun()


def show_confirmation() -> None:
    request = st.session_state.request
    st.subheader(translate_core("review_and_confirm", st.session_state.selected_language).text)
    st.write("Aven will use only this reviewed summary to compare facility records.")

    first, second, third = st.columns(3)
    first.metric("Need", request.get("capability") or request.get("medication_name") or "Not confirmed")
    second.metric("From", request.get("location") or "Not provided")
    third.metric("When", request.get("urgency", "routine").title())
    st.write(
        f"**Preferences:** {request.get('facility_preference', 'either').title()} facilities · "
        f"{request.get('budget_sensitivity', 'medium').title()} cost sensitivity · "
        f"{request.get('travel_tolerance', 'medium').title()} travel tolerance"
    )
    with st.expander("Review all captured details"):
        st.json(request)
        st.caption("Your original text is context from you, not facility evidence.")

    outcome = evaluate_demo_request(request)
    if outcome.safety_branch == SafetyBranch.INCOMPLETE_INTAKE:
        for error in outcome.validation_errors:
            st.error(error)
    elif outcome.safety_branch == SafetyBranch.CONFIRM_CARE_SETTING:
        st.warning(outcome.message)
    elif outcome.safety_branch == SafetyBranch.EMERGENCY:
        show_emergency_stop()
        return

    left, right = st.columns(2)
    with left:
        if st.button("Edit request", use_container_width=True):
            st.session_state.stage = "intake"
            st.rerun()
    with right:
        if st.button(
            "Confirm and find routes",
            type="primary",
            use_container_width=True,
            disabled=outcome.safety_branch != SafetyBranch.PROCEED,
        ):
            st.session_state.outcome = outcome
            st.session_state.stage = "results"
            st.rerun()


def save_option(index: int, option: dict[str, str]) -> None:
    store = SessionLocalPlanStore(st.session_state)
    plan_id = f"demo-plan-{len(st.session_state.saved_plan_ids) + 1}"
    store.save_plan(
        {
            "plan_id": plan_id,
            "request": st.session_state.request,
            "selected_option": option,
            "evidence_origin": "seeded_demo",
        }
    )
    if plan_id not in st.session_state.saved_plan_ids:
        st.session_state.saved_plan_ids.append(plan_id)
    st.session_state.active_plan_id = plan_id
    st.success("Saved in this session. The Databricks deployment can replace this fallback with durable storage.")


def show_travel_truth() -> None:
    provider = select_map_provider()
    chosen_modes = st.session_state.request.get("travel_modes") or []
    with st.expander("Compare travel modes"):
        if not chosen_modes:
            st.write("No travel modes were selected.")
        for mode in chosen_modes:
            capability = mode_capability(provider, mode)
            st.write(f"**{mode.title()}:** {capability.user_label}")
        st.caption(
            "No mode shown here includes a live fare. Transit service, taxi availability, flights, and lodging must be checked before travel."
        )


def show_results() -> None:
    request = st.session_state.request
    outcome = st.session_state.outcome
    st.subheader(translate_core("your_plan", st.session_state.selected_language).text)
    st.caption(f"For {request.get('capability') or request.get('medication_name')} · From {request['location']}")
    st.warning("Seeded demo plan — these cards are not live facility recommendations.")

    st.markdown("### Do this now")
    st.markdown(
        "1. Call the official facility contact once the dataset supplies it.\n"
        "2. Ask whether the exact service is currently available and what it costs.\n"
        "3. Confirm referral, identification, reports, and appointment requirements.\n"
        "4. Verify the route before leaving."
    )

    show_travel_truth()

    for index, option in enumerate(outcome.options):
        with st.container(border=True):
            st.markdown(f"### {option['label']}")
            st.markdown(f"**{option['facility']}**")
            st.write(option["summary"])
            travel_col, cost_col = st.columns(2)
            travel_col.write(f"**Travel**  \n{option['travel']}")
            cost_col.write(f"**Cost**  \n{option['cost']}")
            st.write(f"**What to do next:** {option['next_step']}")
            with st.expander("Why this option? · Evidence Receipt"):
                st.write(f"**Proof state:** {option['evidence']}")
                st.write(f"**What we could not confirm:** {option['unknowns']}")
                st.write(f"**Why it appears here:** {option['ranking']}")
                st.caption("The deployed adapter must show the literal source field, row identifier, and cited span here.")
            if st.button("Save this plan", key=f"save_{index}"):
                save_option(index, option)

    st.subheader("Was this plan useful?")
    feedback = st.radio("Your feedback", ["Helpful", "Needs correction", "Not sure"], horizontal=True)
    note = st.text_input("Optional correction or access note", max_chars=500)
    if st.button("Save feedback"):
        store = SessionLocalPlanStore(st.session_state)
        plan_id = st.session_state.active_plan_id or "demo-preview"
        store.save_feedback(plan_id, {"status": feedback, "note": note})
        st.success("Feedback saved separately from facility evidence.")

    if st.session_state.saved_plan_ids:
        with st.expander("My saved plans"):
            store = SessionLocalPlanStore(st.session_state)
            for plan_id in st.session_state.saved_plan_ids:
                saved = store.get_plan(plan_id)
                if saved:
                    st.write(f"**{plan_id}:** {saved['selected_option']['facility']}")

    if st.button("Start a new request"):
        st.session_state.stage = "intake"
        st.session_state.request = None
        st.session_state.outcome = None
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Aven", page_icon="🧭", layout="centered")
    initialize_state()
    apply_styles()
    show_header()
    show_service_status()
    if st.session_state.stage == "intake":
        show_intake()
    elif st.session_state.stage == "confirm":
        show_confirmation()
    else:
        show_results()


if __name__ == "__main__":
    main()
