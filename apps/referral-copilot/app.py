"""Aven local Streamlit shell.

Run locally with: streamlit run app.py
The demo adapter is deterministic and contains no challenge or patient data.

Screen flow follows docs/ui-handoff.md: Welcome -> Tell us -> Confirm ->
Your plan -> Evidence Receipt -> Save/reopen. Evidence status copy, colors,
and card anatomy match that handoff exactly so the UI stays a thin, honest
client of the domain/demo adapters (no ranking or evidence logic here).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src.demo_adapter import CARE_TASKS, build_demo_options, infer_care_task, next_question
from src.styles import CSS, evidence_badge_html

LANGUAGES = {"en": "English", "hi": "हिंदी", "mr": "मराठी"}

STRINGS = {
    "en": {
        "tagline": "The right care route, with proof.",
        "boundary": "Aven helps plan access to care. It does not diagnose or replace emergency care.",
        "promise": "Tell us what you need. We will help you plan the next step with evidence from facility records.",
        "steps": ["Tell us", "Confirm", "Your plan"],
    },
    "hi": {
        "tagline": "सही देखभाल मार्ग, प्रमाण के साथ।",
        "boundary": "Aven देखभाल तक पहुंच की योजना बनाने में मदद करता है। यह निदान नहीं करता या आपातकालीन देखभाल की जगह नहीं लेता।",
        "promise": "हमें बताएं आपको क्या चाहिए। हम सुविधा रिकॉर्ड के प्रमाण के साथ अगला कदम बनाने में मदद करेंगे।",
        "steps": ["बताएं", "पुष्टि करें", "आपकी योजना"],
    },
    "mr": {
        "tagline": "योग्य काळजी मार्ग, पुराव्यासह.",
        "boundary": "Aven काळजी मिळवण्याचे नियोजन करण्यास मदत करते. हे निदान करत नाही किंवा आपत्कालीन काळजीची जागा घेत नाही.",
        "promise": "तुम्हाला काय हवे आहे ते सांगा. आम्ही सुविधा नोंदींच्या पुराव्यासह पुढील पाऊल ठरवण्यास मदत करू.",
        "steps": ["सांगा", "पुष्टी करा", "तुमची योजना"],
    },
}

EXAMPLE_CHIPS = [
    "I have a referral",
    "Need a test",
    "Need a refill",
    "Need help planning a visit",
]

STEP_KEYS = ["intake", "confirm", "results"]


def t() -> dict:
    return STRINGS[st.session_state.get("language", "en")]


def initialize_state() -> None:
    defaults = {
        "stage": "intake",
        "saved_plans": [],
        "feedback": {},
        "language": "en",
        "draft_message": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def show_header() -> None:
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            f'<div class="aven-header"><p class="aven-title">Aven</p>'
            f'<span class="aven-tagline">{t()["tagline"]}</span></div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        code = st.selectbox(
            "Language",
            options=list(LANGUAGES),
            format_func=lambda k: LANGUAGES[k],
            index=list(LANGUAGES).index(st.session_state.language),
            label_visibility="collapsed",
        )
        if code != st.session_state.language:
            st.session_state.language = code
            st.rerun()

    labels = t()["steps"]
    current = STEP_KEYS.index(st.session_state.stage) if st.session_state.stage in STEP_KEYS else 0
    chips = []
    for index, label in enumerate(labels):
        state = "done" if index < current else ("active" if index == current else "")
        chips.append(f'<div class="aven-step {state}">{index + 1}. {label}</div>')
    st.markdown(f'<div class="aven-stepper">{"".join(chips)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="aven-boundary">{t()["boundary"]}</div>', unsafe_allow_html=True)


def show_intake() -> None:
    st.subheader("Tell us what you need")
    st.caption(t()["promise"])

    chip_cols = st.columns(len(EXAMPLE_CHIPS))
    for col, chip in zip(chip_cols, EXAMPLE_CHIPS):
        if col.button(chip, key=f"chip_{chip}", use_container_width=True):
            st.session_state.draft_message = chip

    message = st.text_area(
        "You can describe your need naturally",
        value=st.session_state.draft_message,
        placeholder="Example: My doctor said I need a cardiology visit and I cannot travel far.",
        key="draft_message",
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
            show_emergency_panel()
            return

    with st.form("intake_form"):
        detail = st.text_input("A little more detail", placeholder=next_question(care_task))
        location = st.text_input("Where are you starting from?", placeholder="City, district, or pincode")
        urgency = st.select_slider("How soon do you need to act?", options=["Routine", "Soon", "Urgent"], value="Soon")
        travel = st.select_slider("How far can you travel?", options=["Low", "Medium", "High"], value="Medium")
        budget = st.select_slider("How important is minimizing cost?", options=["Low", "Medium", "High"], value="High")
        preference = st.radio("Facility preference", options=["Either", "Public", "Private"], horizontal=True)
        language = st.text_input("Preferred language (optional)")
        st.caption("Why do we ask this? Travel and budget preferences change route ordering, not care quality.")
        submitted = st.form_submit_button("Review what Aven understood", type="primary")

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


def show_emergency_panel() -> None:
    st.markdown(
        """
        <div class="aven-emergency">
          <h3>Get urgent help now</h3>
          <p>Seek local emergency care now. Do not wait for a facility comparison.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Start a new non-urgent request"):
        st.session_state.stage = "intake"
        st.session_state.draft_message = ""
        st.rerun()


def show_confirmation() -> None:
    request = st.session_state.request
    st.subheader("Please confirm before we plan")
    st.markdown(
        f"> You are looking for **{request['capability']}** from **{request['location']}**, "
        f"**{request['urgency']}**. You prefer **{request['travel_tolerance']} travel burden** "
        f"and **{request['facility_preference']}** facilities."
    )
    with st.expander("See all fields"):
        st.json(request)
    st.caption("We use your confirmed request to compare documented facility options. We do not infer price, availability, or eligibility.")
    left, right = st.columns(2)
    with left:
        if st.button("Edit request", use_container_width=True):
            st.session_state.stage = "intake"
            st.rerun()
    with right:
        if st.button("Confirm and find routes", type="primary", use_container_width=True):
            st.session_state.options = build_demo_options(request)
            st.session_state.stage = "results"
            st.rerun()


def show_option_card(index: int, option: dict) -> None:
    evidence_status = option.get("evidence_status", "not_documented")
    with st.container():
        st.markdown('<div class="aven-card">', unsafe_allow_html=True)
        top = st.columns([3, 2])
        with top[0]:
            st.markdown(f'<div class="aven-option-label">{option["label"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<p class="aven-facility-name">{option["facility"]}</p>', unsafe_allow_html=True)
        with top[1]:
            st.markdown(evidence_badge_html(evidence_status), unsafe_allow_html=True)

        st.markdown(f'<p class="aven-fact">{option["summary"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>{option["travel"]}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>{option["cost"]}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>What to do next:</strong> {option["next_step"]}</p>', unsafe_allow_html=True)

        button_cols = st.columns(2)
        with button_cols[0]:
            if st.button("Save plan", key=f"save_{index}", use_container_width=True):
                st.session_state.saved_plans.append(option)
                st.success("Saved — reopen it from My plans.")
        with button_cols[1]:
            with st.expander("Why this option?"):
                st.markdown("**What we could not confirm**")
                st.write(option["unknowns"])
                st.markdown("**Ranking explanation**")
                st.caption(option["ranking"])
                st.markdown("**Evidence**")
                st.write(option["evidence"])
        st.markdown("</div>", unsafe_allow_html=True)


def show_results() -> None:
    request = st.session_state.request
    st.subheader("Best next step")
    st.caption(f"For: {request['capability']} · Starting from: {request['location']}")

    options = list(st.session_state.options)
    for option in options:
        option.setdefault(
            "evidence_status",
            {"Best documented fit": "documented", "Lower-burden route": "not_documented", "Alternative to verify": "conflicting"}.get(
                option["label"], "not_documented"
            ),
        )

    for index, option in enumerate(options):
        show_option_card(index, option)

    st.subheader("Was this plan useful?")
    feedback = st.radio("Your feedback", ["Helpful", "Needs correction", "Not sure"], horizontal=True)
    note = st.text_input("Optional correction or note")
    if st.button("Save feedback"):
        st.session_state.feedback = {"status": feedback, "note": note}
        st.success("Feedback saved for this demo session. It does not change facility evidence.")

    if st.session_state.saved_plans:
        st.subheader("My plans")
        for plan in st.session_state.saved_plans:
            st.markdown(f"- **{plan['facility']}** — {plan['label']}")

    if st.button("Start a new request"):
        st.session_state.stage = "intake"
        st.session_state.draft_message = ""
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Aven", page_icon="🧭", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    initialize_state()
    show_header()
    if st.session_state.stage == "intake":
        show_intake()
    elif st.session_state.stage == "confirm":
        show_confirmation()
    else:
        show_results()
    st.markdown(
        '<p class="aven-footer-note">Aven does not diagnose, prescribe, promise prices, or show live availability.</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
