"""Aven local Streamlit shell.

Run locally with: streamlit run app.py
The demo adapter is deterministic and contains no challenge or patient data.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.demo_adapter import CARE_TASKS, build_demo_options, infer_care_task, next_question


def initialize_state() -> None:
    defaults = {"stage": "intake", "saved_plans": [], "feedback": {}}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def show_header() -> None:
    st.title("Aven")
    st.caption("The right care route, with proof.")
    st.info("Demo mode: results are seeded UI examples. Aven does not diagnose, prescribe, promise prices, or show live availability.")


def show_intake() -> None:
    st.subheader("Tell us what you need")
    message = st.text_area(
        "You can describe your need naturally",
        placeholder="Example: My doctor said I need a cardiology visit and I cannot travel far.",
    )
    inferred = infer_care_task(message)
    care_task = st.selectbox(
        "What kind of help do you need?",
        options=list(CARE_TASKS),
        index=list(CARE_TASKS).index(inferred),
        format_func=lambda value: CARE_TASKS[value],
    )

    if care_task == "symptom_first":
        st.warning("If you think this may be an emergency, seek urgent local help now. Aven cannot assess or diagnose symptoms.")
        emergency = st.checkbox("I have a possible emergency warning sign or need immediate help")
        if emergency:
            st.error("Please seek emergency care or contact local emergency services now. This demo will not create an ordinary facility ranking.")
            return

    with st.form("intake_form"):
        detail = st.text_input("A little more detail", placeholder=next_question(care_task))
        location = st.text_input("Where are you starting from?", placeholder="City, district, or pincode")
        urgency = st.select_slider("How soon do you need to act?", options=["Routine", "Soon", "Urgent"], value="Soon")
        travel = st.select_slider("How far can you travel?", options=["Low", "Medium", "High"], value="Medium")
        budget = st.select_slider("How important is minimizing cost?", options=["Low", "Medium", "High"], value="High")
        preference = st.radio("Facility preference", options=["Either", "Public", "Private"], horizontal=True)
        language = st.text_input("Preferred language (optional)")
        submitted = st.form_submit_button("Review what Aven understood")

    if submitted:
        st.session_state.request = {
            "message": message,
            "care_task": care_task,
            "capability": detail or message or "the care need you described",
            "location": location or "not provided",
            "urgency": urgency.lower(),
            "travel_tolerance": travel.lower(),
            "budget_sensitivity": budget.lower(),
            "facility_preference": preference.lower(),
            "language": language or "not specified",
        }
        st.session_state.stage = "confirm"
        st.rerun()


def show_confirmation() -> None:
    request = st.session_state.request
    st.subheader("Please confirm before we plan")
    st.write("Aven will use this summary to look for care-access options:")
    st.json(request)
    left, right = st.columns(2)
    with left:
        if st.button("Back and edit"):
            st.session_state.stage = "intake"
            st.rerun()
    with right:
        if st.button("Confirm and show demo plan", type="primary"):
            st.session_state.options = build_demo_options(request)
            st.session_state.stage = "results"
            st.rerun()


def show_results() -> None:
    request = st.session_state.request
    st.subheader("Your next-step plan")
    st.caption(f"For: {request['capability']} · Starting from: {request['location']}")
    for index, option in enumerate(st.session_state.options):
        with st.container(border=True):
            st.markdown(f"### {option['label']}: {option['facility']}")
            st.write(option["summary"])
            st.write(f"**{option['travel']}**")
            st.write(f"**{option['cost']}**")
            st.write(f"**What to do next:** {option['next_step']}")
            with st.expander("Why this option?"):
                st.write(option["evidence"])
                st.write(f"**What still needs checking:** {option['unknowns']}")
                st.caption(option["ranking"])
            if st.button("Save this option", key=f"save_{index}"):
                st.session_state.saved_plans.append(option)
                st.success("Saved in this demo session. Lakebase will replace this temporary storage in the deployed app.")

    st.subheader("Was this plan useful?")
    feedback = st.radio("Your feedback", ["Helpful", "Needs correction", "Not sure"], horizontal=True)
    note = st.text_input("Optional correction or note")
    if st.button("Save feedback"):
        st.session_state.feedback = {"status": feedback, "note": note}
        st.success("Feedback saved for this demo session. It does not change facility evidence.")

    if st.session_state.saved_plans:
        st.subheader("Saved in this session")
        st.write([plan["facility"] for plan in st.session_state.saved_plans])

    if st.button("Start a new request"):
        st.session_state.stage = "intake"
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Aven", page_icon="🧭", layout="centered")
    initialize_state()
    show_header()
    if st.session_state.stage == "intake":
        show_intake()
    elif st.session_state.stage == "confirm":
        show_confirmation()
    else:
        show_results()


if __name__ == "__main__":
    main()
