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
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from src import profiles
from src.demo_adapter import CARE_TASKS, build_demo_options, next_question
from src.styles import (
    CSS,
    ECG_DIVIDER_SVG,
    FONT_IMPORT,
    LOGO_PULSE_SVG,
    SCROLL_REVEAL_JS,
    card_classes,
    evidence_badge_html,
    marquee_html,
    option_icon,
)

LANGUAGES = {"en": "English", "hi": "हिंदी", "mr": "मराठी"}

STRINGS = {
    "en": {
        "tagline": "The right care route, with proof.",
        "boundary": "Aven helps plan access to care. It does not diagnose or replace emergency care.",
        "promise": "Tell us what you need. We will help you plan the next step with evidence from facility records.",
        "steps": ["Tell us", "Confirm", "Your plan"],
        "vitals": "Connected across facility networks",
        "eyebrow": "Care Navigation · Evidence-Backed",
    },
    "hi": {
        "tagline": "सही देखभाल मार्ग, प्रमाण के साथ।",
        "boundary": "Aven देखभाल तक पहुंच की योजना बनाने में मदद करता है। यह निदान नहीं करता या आपातकालीन देखभाल की जगह नहीं लेता।",
        "promise": "हमें बताएं आपको क्या चाहिए। हम सुविधा रिकॉर्ड के प्रमाण के साथ अगला कदम बनाने में मदद करेंगे।",
        "steps": ["बताएं", "पुष्टि करें", "आपकी योजना"],
        "vitals": "सुविधा नेटवर्क में सक्रिय रूप से जुड़ा हुआ",
        "eyebrow": "देखभाल मार्गदर्शन · प्रमाण-आधारित",
    },
    "mr": {
        "tagline": "योग्य काळजी मार्ग, पुराव्यासह.",
        "boundary": "Aven काळजी मिळवण्याचे नियोजन करण्यास मदत करते. हे निदान करत नाही किंवा आपत्कालीन काळजीची जागा घेत नाही.",
        "promise": "तुम्हाला काय हवे आहे ते सांगा. आम्ही सुविधा नोंदींच्या पुराव्यासह पुढील पाऊल ठरवण्यास मदत करू.",
        "steps": ["सांगा", "पुष्टी करा", "तुमची योजना"],
        "vitals": "सुविधा नेटवर्कमध्ये सक्रियपणे जोडलेले",
        "eyebrow": "काळजी मार्गदर्शन · पुरावा-आधारित",
    },
}

STEP_KEYS = ["intake", "confirm", "results"]

# Landing-page copy. Only English is authored here; tx() falls back to English
# for any language missing a key so the flow stays localized while the marketing
# surface degrades gracefully.
LANDING_COPY = {
    "en": {
        "hero_tagline": "The right care route — <em>with its receipts.</em>",
        "hero_sub": "Describe a care need in plain words. Aven plans the next step and shows the evidence behind it.",
        "scroll_cue": "Scroll",
        "nav_cta": "Explore",
        "marquee": [
            "The right route, revealed",
            "Care that comes with its receipts",
            "Honest about the unknowns",
            "Evidence you can see",
        ],
        "statement_kicker": "The idea",
        "statement": (
            'A care need becomes <span class="dim">a clear request, an actionable route,</span> '
            'and the proof behind every option.'
        ),
        "about_eyebrow": "How it works",
        "about_title": "Care that comes with its receipts.",
        "about_body": (
            "Describe a care-access need in plain words. Aven turns it into a clear, "
            "structured request, then plans an actionable route — showing the evidence "
            "behind every option and being honest about what it could not confirm."
        ),
        "about_points": [
            ("Say it your way", "Type naturally in English, Hindi, or Marathi. No forms to decode."),
            ("See the proof", "Every option shows what is documented, what conflicts, and what is unknown."),
            ("Plan the next step", "Compare routes by travel and cost, then save a plan to act on."),
        ],
        "tiles_eyebrow": "Choose a starting point",
        "tiles_title": "What do you need today?",
        "tiles_hint": "Each path opens its own form — you can switch between them anytime.",
    }
}

# Each tile maps to a real care task in the domain adapter (plus one saved-plans
# shortcut). Clicking a tile presets that task and enters the intake flow.
FEATURE_TILES = [
    {"key": "known_referral", "icon": "🩺", "title": "Referral or procedure",
     "desc": "Plan a route for a specialty visit or procedure your doctor referred.",
     "detail_label": "What did your doctor refer you for?"},
    {"key": "refill", "icon": "💊", "title": "Medication refill",
     "desc": "Find where to refill a prescription or reach a pharmacy.",
     "detail_label": "What medication do you need refilled?"},
    {"key": "lab", "icon": "🧪", "title": "Lab or blood test",
     "desc": "Locate a facility for a test or blood draw your clinician requested.",
     "detail_label": "What test or blood draw was requested?"},
    {"key": "follow_up", "icon": "📅", "title": "Follow-up question",
     "desc": "Reconnect with a facility or doctor about an appointment.",
     "detail_label": "Which facility or doctor are you trying to reach?"},
    {"key": "symptom_first", "icon": "🧭", "title": "Not sure what I need",
     "desc": "Talk it through and plan a safe next step. This is not a diagnosis.",
     "detail_label": "What is worrying you today?"},
]

TASK_META = {tile["key"]: tile for tile in FEATURE_TILES}


def t() -> dict:
    return STRINGS[st.session_state.get("language", "en")]


def tx(key: str) -> object:
    """Landing copy lookup with English fallback for untranslated keys."""
    language = st.session_state.get("language", "en")
    return LANDING_COPY.get(language, {}).get(key, LANDING_COPY["en"][key])


def initialize_state() -> None:
    defaults = {
        "stage": "landing",
        "saved_plans": [],
        "feedback": {},
        "language": "en",
        "draft_message": "",
        "preset_care_task": None,
        "user": None,  # None = guest; otherwise {"name", "email"}
        "profile": profiles.empty_profile(),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ---------- Profile helpers ----------

def current_profile() -> dict:
    return st.session_state.profile


def is_logged_in() -> bool:
    return st.session_state.user is not None


def persist_profile() -> None:
    """Save to disk only for logged-in users; guests stay session-only."""
    if is_logged_in():
        profiles.save_profile(st.session_state.profile)


def do_login(name: str, email: str) -> None:
    email = email.strip()
    profile = profiles.load_profile(email)
    if name.strip():
        profile["name"] = name.strip()
    st.session_state.profile = profile
    st.session_state.user = {"name": profile.get("name") or "Member", "email": email}
    profiles.save_profile(profile)
    st.rerun()


def do_logout() -> None:
    st.session_state.user = None
    st.session_state.profile = profiles.empty_profile()
    st.session_state.stage = "landing"
    st.rerun()


def go_to_intake(care_task: str | None = None) -> None:
    """Enter the intake flow, optionally preselecting a care task from a tile."""
    st.session_state.preset_care_task = care_task
    st.session_state.stage = "intake"
    st.rerun()


def _go_home() -> None:
    st.session_state.stage = "landing"
    st.rerun()


def show_header_bar() -> None:
    """Sticky interactive header shown on every view: the AVEN wordmark, page
    links, a Forms dropdown that jumps straight into any form, and the language
    picker. Rendered with real Streamlit widgets inside a keyed container that
    CSS makes sticky and full-bleed."""
    with st.container(key="aven_header"):
        has_saved = bool(st.session_state.saved_plans)
        # brand | home | forms | [saved] | spacer | language | account
        if has_saved:
            widths = [1.5, 0.7, 0.9, 0.9, 0.5, 1.0, 1.0]
        else:
            widths = [1.7, 0.8, 1.0, 0.6, 1.1, 1.1]
        cols = st.columns(widths, vertical_alignment="center")
        idx = 0

        with cols[idx]:
            if st.button("Aven", key="brand_home"):
                _go_home()
        idx += 1
        with cols[idx]:
            if st.button("Home", key="page_home"):
                _go_home()
        idx += 1
        with cols[idx]:
            with st.popover("Forms", use_container_width=True):
                st.markdown("**Choose a form**")
                for tile in FEATURE_TILES:
                    if st.button(f"{tile['icon']}  {tile['title']}", key=f"navform_{tile['key']}", use_container_width=True):
                        go_to_intake(tile["key"])
        idx += 1
        if has_saved:
            with cols[idx]:
                if st.button("Saved", key="page_saved"):
                    st.session_state.stage = "results"
                    st.rerun()
            idx += 1

        idx += 1  # skip the spacer column
        with cols[idx]:
            code = st.selectbox(
                "Language",
                options=list(LANGUAGES),
                format_func=lambda k: LANGUAGES[k],
                index=list(LANGUAGES).index(st.session_state.language),
                label_visibility="collapsed",
                key="lang_header",
            )
            if code != st.session_state.language:
                st.session_state.language = code
                st.rerun()
        idx += 1
        with cols[idx]:
            show_account_control()


def show_account_control() -> None:
    """Login / profile control pinned to the top-right corner. Guests can use
    Aven fully; logging in just persists history, ratings, and the blocklist."""
    if is_logged_in():
        first = (st.session_state.user["name"].split() or ["Member"])[0]
        with st.popover(f"👤 {first}", use_container_width=True):
            st.markdown(f"**Signed in** · {st.session_state.user['email']}")
            if st.button("My profile", key="acct_profile", use_container_width=True):
                st.session_state.stage = "profile"
                st.rerun()
            if st.button("Log out", key="acct_logout", use_container_width=True):
                do_logout()
    else:
        with st.popover("Log in", use_container_width=True):
            st.markdown("**Log in to Aven**")
            st.caption("No account needed — you can submit forms as a guest. Log in to keep your history, hospital ratings, and blocked facilities across visits.")
            name = st.text_input("Name", key="login_name", placeholder="Your name")
            email = st.text_input("Email", key="login_email", placeholder="you@example.com")
            if st.button("Log in", key="login_submit", type="primary", use_container_width=True):
                if email.strip():
                    do_login(name, email)
                else:
                    st.warning("Enter an email to log in, or just close this and continue as a guest.")
            if st.button("View my activity (guest)", key="guest_activity", use_container_width=True):
                st.session_state.stage = "profile"
                st.rerun()


def show_landing() -> None:
    show_header_bar()

    # Full-bleed editorial hero: oversized wordmark + poetic tagline + ECG hairline.
    st.markdown(
        f'<div class="aven-hero-full">'
        f'<div class="aven-hero-inner">'
        f'<span class="aven-eyebrow">{LOGO_PULSE_SVG}{t()["eyebrow"]}</span>'
        f'<h1 class="aven-display">Aven</h1>'
        f'{ECG_DIVIDER_SVG}'
        f'<p class="aven-hero-tagline">{tx("hero_tagline")}</p>'
        f'<p class="aven-hero-sub">{tx("hero_sub")}</p>'
        f'<a class="aven-scroll-cue" href="#aven-statement">'
        f'<span>{tx("scroll_cue")}</span><span class="aven-chevron">⌄</span></a>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # Marquee ticker.
    st.markdown(marquee_html(list(tx("marquee"))), unsafe_allow_html=True)

    # Big statement section.
    st.markdown(
        f'<div id="aven-statement" class="aven-statement aven-reveal">'
        f'<span class="aven-section-title">{tx("statement_kicker")}</span>'
        f'<p class="aven-statement-text">{tx("statement")}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Numbered principles.
    points = "".join(
        f'<div class="aven-about-point aven-reveal stagger-{i}">'
        f'<div class="aven-about-point-num">/ 0{i + 1}</div>'
        f"<h4>{title}</h4><p>{body}</p></div>"
        for i, (title, body) in enumerate(tx("about_points"))
    )
    st.markdown(
        f'<div id="aven-about" class="aven-about">'
        f'<div class="aven-reveal">'
        f'<span class="aven-section-title">{tx("about_eyebrow")}</span>'
        f'<h2 class="aven-about-title">{tx("about_title")}</h2>'
        f'<p class="aven-about-body">{tx("about_body")}</p></div>'
        f'<div class="aven-about-points">{points}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    show_tiles()


def show_tiles() -> None:
    st.markdown(
        f'<div id="aven-tiles" class="aven-tiles-head aven-reveal">'
        f'<span class="aven-section-title">{tx("tiles_eyebrow")}</span>'
        f'<h2 class="aven-about-title">{tx("tiles_title")}</h2>'
        f'<p class="aven-tiles-hint">{tx("tiles_hint")}</p></div>',
        unsafe_allow_html=True,
    )

    tiles = list(FEATURE_TILES)
    if st.session_state.saved_plans:
        tiles.append({"key": "__saved", "icon": "📁", "title": "My saved plans",
                      "desc": f"Reopen the {len(st.session_state.saved_plans)} route(s) you saved this session."})

    # Render tiles as a real button grid. Each button's parent gets a
    # `st-key-tile_*` class from Streamlit, which the CSS targets to style the
    # button as a large, hoverable card while keeping full session state.
    for row_start in range(0, len(tiles), 3):
        row = tiles[row_start:row_start + 3]
        cols = st.columns(3)
        for col, tile in zip(cols, row):
            cta = "Open plans →" if tile["key"] == "__saved" else "Open form →"
            label = f"{tile['icon']}\n\n**{tile['title']}**\n\n{tile['desc']}\n\n{cta}"
            if col.button(label, key=f"tile_{tile['key']}", use_container_width=True):
                if tile["key"] == "__saved":
                    st.session_state.stage = "results"
                    st.rerun()
                else:
                    go_to_intake(tile["key"])


def show_flow_header() -> None:
    """Header + step tracker for the intake/confirm/results flow. Home, Forms,
    and language all live in the global header bar now."""
    show_header_bar()

    labels = t()["steps"]
    current = STEP_KEYS.index(st.session_state.stage) if st.session_state.stage in STEP_KEYS else 0
    chips = []
    for index, label in enumerate(labels):
        state = "done" if index < current else ("active" if index == current else "")
        mark = "✓ " if state == "done" else f"{index + 1}. "
        chips.append(f'<div class="aven-step {state}">{mark}{label}</div>')
    st.markdown(f'<div class="aven-stepper">{"".join(chips)}</div>', unsafe_allow_html=True)


def show_task_switcher(active: str) -> None:
    """A row of task pills so it is always clear which form you are in and that
    other forms exist — you can switch without going back to the landing page."""
    st.markdown('<div class="aven-switcher-label">Choose the form for your need</div>', unsafe_allow_html=True)
    cols = st.columns(len(FEATURE_TILES))
    for col, tile in zip(cols, FEATURE_TILES):
        is_active = tile["key"] == active
        if col.button(
            f"{tile['icon']} {tile['title']}",
            key=f"taskchip_{tile['key']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.care_task = tile["key"]
            st.rerun()


def show_intake() -> None:
    # Resolve the active form: a tile preset wins on first entry, otherwise the
    # last chosen task persists across reruns.
    preset = st.session_state.pop("preset_care_task", None)
    if preset in CARE_TASKS:
        st.session_state.care_task = preset
    care_task = st.session_state.setdefault("care_task", "known_referral")
    meta = TASK_META[care_task]

    show_task_switcher(care_task)

    # Distinct, branded header so each form clearly stands on its own.
    st.markdown(
        f'<div class="aven-form-head">'
        f'<div class="aven-form-icon">{meta["icon"]}</div>'
        f'<div><h2 class="aven-form-title">{meta["title"]}</h2>'
        f'<p class="aven-form-blurb">{meta["desc"]}</p></div></div>',
        unsafe_allow_html=True,
    )

    if care_task == "symptom_first":
        st.warning("If you think this may be an emergency, seek urgent local help now. Aven cannot assess or diagnose symptoms.")
        emergency = st.checkbox("I have a possible emergency warning sign or need immediate help")
        if emergency:
            show_emergency_panel()
            return

    st.markdown('<div class="aven-reveal">', unsafe_allow_html=True)
    with st.form("intake_form"):
        st.markdown('<div class="aven-section-title">The specifics</div>', unsafe_allow_html=True)
        detail = st.text_input(meta["detail_label"], placeholder=next_question(care_task))
        location = st.text_input("Where are you starting from?", placeholder="City, district, or pincode")
        message = st.text_area(
            "Anything else we should know? (optional)",
            placeholder="Example: My doctor said I need a cardiology visit and I cannot travel far.",
        )

        st.markdown('<div class="aven-section-title">Your preferences</div>', unsafe_allow_html=True)
        st.caption("Why do we ask this? Travel and budget preferences change route ordering, not care quality.")
        pref_left, pref_right = st.columns(2)
        with pref_left:
            urgency = st.select_slider("How soon do you need to act?", options=["Routine", "Soon", "Urgent"], value="Soon")
            travel = st.select_slider("How far can you travel?", options=["Low", "Medium", "High"], value="Medium")
        with pref_right:
            budget = st.select_slider("How important is minimizing cost?", options=["Low", "Medium", "High"], value="High")
            preference = st.radio("Facility preference", options=["Either", "Public", "Private"], horizontal=True)
        language = st.text_input("Preferred language (optional)")
        submitted = st.form_submit_button("Review what Aven understood", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

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
    st.markdown('<div class="aven-reveal">', unsafe_allow_html=True)
    st.markdown('<div class="aven-section-title">Please confirm before we plan</div>', unsafe_allow_html=True)
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
            profiles.add_history(current_profile(), request)
            persist_profile()
            st.session_state.stage = "results"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_option_card(index: int, option: dict) -> None:
    evidence_status = option.get("evidence_status", "not_documented")
    profile = current_profile()
    facility = option["facility"]
    rating = profiles.get_rating(profile, facility)
    with st.container():
        st.markdown(f'<div class="{card_classes(index)}">', unsafe_allow_html=True)
        top = st.columns([3, 2])
        with top[0]:
            st.markdown(
                f'<div class="aven-option-label">{option_icon(option["label"])} {option["label"]}</div>',
                unsafe_allow_html=True,
            )
            name_extra = f' <span class="aven-rating-badge">★ {rating}/5</span>' if rating else ""
            st.markdown(f'<p class="aven-facility-name">{facility}{name_extra}</p>', unsafe_allow_html=True)
        with top[1]:
            st.markdown(evidence_badge_html(evidence_status), unsafe_allow_html=True)

        st.markdown(f'<p class="aven-fact">{option["summary"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>{option["travel"]}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>{option["cost"]}</strong></p>', unsafe_allow_html=True)
        st.markdown(f'<p class="aven-fact"><strong>What to do next:</strong> {option["next_step"]}</p>', unsafe_allow_html=True)

        button_cols = st.columns([1, 1, 1])
        with button_cols[0]:
            if st.button("Save plan", key=f"save_{index}", use_container_width=True):
                already_saved = any(plan["facility"] == facility for plan in st.session_state.saved_plans)
                st.session_state.saved_plans.append(option)
                profiles.add_saved(profile, option, st.session_state.request.get("care_task", ""))
                persist_profile()
                st.success("Saved — reopen it from My plans.")
                if not already_saved:
                    st.balloons()
        with button_cols[1]:
            if st.button("🚫 Never refer me here", key=f"block_{index}", use_container_width=True):
                profiles.block_facility(profile, facility)
                persist_profile()
                st.rerun()
        with button_cols[2]:
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
    st.markdown('<div class="aven-section-title">Best next step</div>', unsafe_allow_html=True)
    st.caption(f"For: {request['capability']} · Starting from: {request['location']}")

    options = list(st.session_state.options)
    for option in options:
        option.setdefault(
            "evidence_status",
            {"Best documented fit": "documented", "Lower-burden route": "not_documented", "Alternative to verify": "conflicting"}.get(
                option["label"], "not_documented"
            ),
        )

    # Honor the user's blocklist: never show a facility they asked never to see.
    profile = current_profile()
    visible = [o for o in options if not profiles.is_blocked(profile, o["facility"])]
    hidden = len(options) - len(visible)
    if hidden:
        st.markdown(
            f'<div class="aven-blocked-note">🚫 {hidden} option(s) hidden because you asked not to be referred there. '
            f'Manage this in your profile.</div>',
            unsafe_allow_html=True,
        )

    if not visible:
        st.info("Every documented option here is on your blocklist. Unblock a facility in your profile to see routes again.")

    for index, option in enumerate(visible):
        show_option_card(index, option)

    st.markdown('<div class="aven-reveal">', unsafe_allow_html=True)
    st.markdown('<div class="aven-section-title">Was this plan useful?</div>', unsafe_allow_html=True)
    feedback = st.radio("Your feedback", ["Helpful", "Needs correction", "Not sure"], horizontal=True)
    note = st.text_input("Optional correction or note")
    if st.button("Save feedback"):
        st.session_state.feedback = {"status": feedback, "note": note}
        st.success("Feedback saved for this demo session. It does not change facility evidence.")

    if st.session_state.saved_plans:
        st.markdown('<div class="aven-section-title">My plans</div>', unsafe_allow_html=True)
        for plan in st.session_state.saved_plans:
            st.markdown(f"- {option_icon(plan['label'])} **{plan['facility']}** — {plan['label']}")

    if st.button("Start a new request"):
        st.session_state.stage = "intake"
        st.session_state.draft_message = ""
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_profile() -> None:
    profile = current_profile()
    logged_in = is_logged_in()

    who = st.session_state.user["name"] if logged_in else "Guest"
    st.markdown(
        f'<div class="aven-profile-head">'
        f'<span class="aven-section-title">Your profile</span>'
        f'<h2 class="aven-about-title">Hello, {who}.</h2>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if not logged_in:
        st.info("You're browsing as a guest. Log in (top-right) to keep your history, ratings, and blocked facilities across visits.")

    stat_cols = st.columns(3)
    stat_cols[0].metric("Requests made", len(profile["history"]))
    stat_cols[1].metric("Saved referrals", len(profile["saved"]))
    stat_cols[2].metric("Blocked facilities", len(profile["blocklist"]))

    if st.button("＋ Start a new request", type="primary"):
        go_to_intake(None)

    # --- Blocklist ---
    st.markdown('<div class="aven-section-title">Facilities you blocked</div>', unsafe_allow_html=True)
    if profile["blocklist"]:
        st.caption("Aven will never include these in your routes. Remove one to allow it again.")
        for i, facility in enumerate(list(profile["blocklist"])):
            row = st.columns([4, 1], vertical_alignment="center")
            row[0].markdown(f"🚫 **{facility}**")
            if row[1].button("Unblock", key=f"unblock_{i}", use_container_width=True):
                profiles.unblock_facility(profile, facility)
                persist_profile()
                st.rerun()
    else:
        st.caption("None yet. On any result you can tap “Never refer me here”.")

    # --- Saved referrals + ratings ---
    st.markdown('<div class="aven-section-title">Saved referrals & ratings</div>', unsafe_allow_html=True)
    if profile["saved"]:
        for i, item in enumerate(profile["saved"]):
            facility = item["facility"]
            with st.container():
                st.markdown(f'<div class="aven-profile-card">', unsafe_allow_html=True)
                st.markdown(
                    f'<p class="aven-facility-name">{facility}</p>'
                    f'<p class="aven-fact">{CARE_TASKS.get(item.get("care_task",""), "Saved route")} · {item.get("label","")}</p>',
                    unsafe_allow_html=True,
                )
                rate_col, block_col = st.columns([2, 1], vertical_alignment="center")
                with rate_col:
                    st.caption("Rate this hospital")
                    stored = profiles.get_rating(profile, facility)
                    rkey = f"prate_{i}_{facility}"
                    st.session_state.setdefault(rkey, (stored - 1) if stored else None)
                    chosen = st.feedback("stars", key=rkey)
                    if chosen is not None and (stored is None or chosen + 1 != stored):
                        profiles.set_rating(profile, facility, chosen + 1)
                        persist_profile()
                        st.rerun()
                with block_col:
                    if facility in profile["blocklist"]:
                        if st.button("Unblock", key=f"psaved_unblock_{i}", use_container_width=True):
                            profiles.unblock_facility(profile, facility)
                            persist_profile()
                            st.rerun()
                    else:
                        if st.button("🚫 Never again", key=f"psaved_block_{i}", use_container_width=True):
                            profiles.block_facility(profile, facility)
                            persist_profile()
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("No saved referrals yet. Save a route from your results to rate it later.")

    # --- History ---
    st.markdown('<div class="aven-section-title">Past requests</div>', unsafe_allow_html=True)
    if profile["history"]:
        for entry in profile["history"]:
            when = time.strftime("%d %b, %H:%M", time.localtime(entry.get("ts", time.time())))
            task = CARE_TASKS.get(entry.get("care_task", ""), "Request")
            st.markdown(
                f'<div class="aven-history-row"><span class="aven-history-when">{when}</span>'
                f'<span><strong>{task}</strong> — {entry.get("capability","")} '
                f'<span class="dim">· from {entry.get("location","")}</span></span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Nothing here yet. Your submitted requests will show up here.")


def main() -> None:
    st.set_page_config(page_title="Aven", page_icon="🩺", layout="centered")
    st.markdown(FONT_IMPORT, unsafe_allow_html=True)
    st.markdown(CSS, unsafe_allow_html=True)
    initialize_state()

    stage = st.session_state.stage
    # Guard: results needs a built request; fall back to intake if navigated
    # there without one (e.g. a stale saved-plans shortcut).
    if stage == "results" and "options" not in st.session_state:
        stage = st.session_state.stage = "intake"

    if stage == "landing":
        show_landing()
    elif stage == "profile":
        show_header_bar()
        show_profile()
    else:
        show_flow_header()
        if stage == "intake":
            show_intake()
        elif stage == "confirm":
            show_confirmation()
        else:
            show_results()

    st.markdown(
        f'<div class="aven-footer">'
        f'<p class="aven-footer-boundary">🛡️ {t()["boundary"]}</p>'
        f'<p class="aven-footer-note">Aven does not diagnose, prescribe, promise prices, or show live availability.</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    # Injected last so every .aven-reveal element above already exists in the
    # DOM by the time this script runs and starts observing them.
    components.html(SCROLL_REVEAL_JS, height=0)


if __name__ == "__main__":
    main()
