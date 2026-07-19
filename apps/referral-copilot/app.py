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

from src import enrichment as enrich
from src import profiles
from src.backend import service as backend
from src.demo_adapter import CARE_TASKS, next_question
from src.localization import SUPPORTED_LANGUAGES, resolve_language
from src.ui_contract import AvenUiBackend
from src.styles import (
    CSS,
    ECG_DIVIDER_SVG,
    FONT_IMPORT,
    LOGO_PULSE_SVG,
    SCROLL_REVEAL_JS,
    card_classes,
    chips_html,
    claim_html,
    evidence_badge_html,
    marquee_html,
    option_icon,
    quality_note_html,
)

# Language names come from src/localization.py — the module that owns approved
# translations — so the picker can never drift from what is actually translatable.
LANGUAGES = SUPPORTED_LANGUAGES

# Bounded feedback vocabulary. Labels are ours; the values must stay inside the
# façade's accepted statuses (tests/test_ui_contract_alignment.py enforces this),
# so a future switch to AvenUiBackend.save_feedback needs no data migration.
FEEDBACK_OPTIONS = {
    "It was helpful": "helpful",
    "Something needs correction": "needs_correction",
    "I am not sure yet": "not_sure",
    "The service was not available": "service_unavailable",
    "The price was different": "price_differed",
    "I went to this facility": "accepted",
    "I did not go": "not_visited",
}

STRINGS = {
    "en": {
        "tagline": "The right care route, with proof.",
        "boundary": "Aven helps plan access to care — it does not diagnose, prescribe, promise prices, show live availability, or replace emergency care.",
        "promise": "Tell us what you need. We will help you plan the next step with evidence from facility records.",
        "steps": ["Tell us", "Confirm", "Your plan"],
        "vitals": "Connected across facility networks",
        "eyebrow": "Care Navigation · Evidence-Backed",
    },
    "hi": {
        "tagline": "सही देखभाल मार्ग, प्रमाण के साथ।",
        "boundary": "Aven देखभाल तक पहुंच की योजना बनाने में मदद करता है — यह निदान नहीं करता, दवा नहीं लिखता, कीमतों का वादा नहीं करता, लाइव उपलब्धता नहीं दिखाता, और न ही आपातकालीन देखभाल की जगह लेता है।",
        "promise": "हमें बताएं आपको क्या चाहिए। हम सुविधा रिकॉर्ड के प्रमाण के साथ अगला कदम बनाने में मदद करेंगे।",
        "steps": ["बताएं", "पुष्टि करें", "आपकी योजना"],
        "vitals": "सुविधा नेटवर्क में सक्रिय रूप से जुड़ा हुआ",
        "eyebrow": "देखभाल मार्गदर्शन · प्रमाण-आधारित",
    },
    "mr": {
        "tagline": "योग्य काळजी मार्ग, पुराव्यासह.",
        "boundary": "Aven काळजी मिळवण्याचे नियोजन करण्यास मदत करते — हे निदान करत नाही, औषध लिहून देत नाही, किमतींचे आश्वासन देत नाही, थेट उपलब्धता दाखवत नाही किंवा आपत्कालीन काळजीची जागा घेत नाही.",
        "promise": "तुम्हाला काय हवे आहे ते सांगा. आम्ही सुविधा नोंदींच्या पुराव्यासह पुढील पाऊल ठरवण्यास मदत करू.",
        "steps": ["सांगा", "पुष्टी करा", "तुमची योजना"],
        "vitals": "सुविधा नेटवर्कमध्ये सक्रियपणे जोडलेले",
        "eyebrow": "काळजी मार्गदर्शन · पुरावा-आधारित",
    },
}

STEP_KEYS = ["intake", "confirm", "results"]

# All non-flow UI copy. tx() falls back to English per key, so a missing
# translation degrades to English instead of raising or rendering blank.
UI_COPY = {
    "hi": {
        "hero_tagline": "सही देखभाल मार्ग — <em>प्रमाण के साथ।</em>",
        "hero_sub": "अपनी ज़रूरत सरल शब्दों में बताएं। Aven अगला कदम तय करता है और उसके पीछे का प्रमाण दिखाता है।",
        "scroll_cue": "नीचे देखें",
        "nav_cta": "देखें",
        "marquee": [
            "सही मार्ग, स्पष्ट रूप से",
            "देखभाल, प्रमाण के साथ",
            "अनिश्चितताओं के बारे में ईमानदार",
            "प्रमाण जो आप देख सकें",
        ],
        "statement_kicker": "विचार",
        "statement": (
            'देखभाल की ज़रूरत बनती है <span class="dim">एक स्पष्ट अनुरोध, एक व्यावहारिक मार्ग,</span> '
            'और हर विकल्प के पीछे का प्रमाण।'
        ),
        "about_eyebrow": "यह कैसे काम करता है",
        "about_title": "देखभाल, जो प्रमाण के साथ आती है।",
        "about_body": (
            "देखभाल तक पहुंच की अपनी ज़रूरत सरल शब्दों में बताएं। Aven उसे एक स्पष्ट, संरचित "
            "अनुरोध में बदलता है, फिर एक व्यावहारिक मार्ग बनाता है — हर विकल्प के पीछे का प्रमाण "
            "दिखाते हुए और जो पुष्टि नहीं हो सकी उसके बारे में ईमानदार रहते हुए।"
        ),
        "about_points": [
            ("अपने शब्दों में कहें", "अंग्रेज़ी, हिंदी या मराठी में सहज रूप से लिखें। कोई जटिल फ़ॉर्म नहीं।"),
            ("प्रमाण देखें", "हर विकल्प दिखाता है कि क्या प्रलेखित है, क्या विरोधाभासी है, और क्या अज्ञात है।"),
            ("अगला कदम तय करें", "यात्रा और लागत के आधार पर मार्गों की तुलना करें, फिर योजना सहेजें।"),
        ],
        "tiles_eyebrow": "शुरुआत चुनें",
        "tiles_title": "आज आपको क्या चाहिए?",
        "tiles_hint": "हर विकल्प अपना फ़ॉर्म खोलता है — आप कभी भी बदल सकते हैं।",
        "switcher_label": "अपनी ज़रूरत के लिए फ़ॉर्म चुनें",
        "specifics": "विवरण",
        "location_label": "आप कहां से शुरू कर रहे हैं?",
        "location_ph": "शहर, ज़िला या पिनकोड",
        "extra_label": "और कुछ जो हमें जानना चाहिए? (वैकल्पिक)",
        "extra_ph": "उदाहरण: डॉक्टर ने हृदय रोग विशेषज्ञ से मिलने को कहा है और मैं दूर यात्रा नहीं कर सकता।",
        "prefs": "आपकी प्राथमिकताएं",
        "prefs_why": "हम यह क्यों पूछते हैं? यात्रा और बजट प्राथमिकताएं मार्गों का क्रम बदलती हैं, देखभाल की गुणवत्ता नहीं।",
        "urgency_label": "आपको कितनी जल्दी कार्रवाई करनी है?",
        "travel_label": "आप कितनी दूर यात्रा कर सकते हैं?",
        "budget_label": "लागत कम करना कितना महत्वपूर्ण है?",
        "facility_label": "सुविधा प्राथमिकता",
        "language_label": "पसंदीदा भाषा (वैकल्पिक)",
        "submit": "देखें Aven ने क्या समझा",
        "confirm_title": "योजना बनाने से पहले पुष्टि करें",
        "confirm_edit": "अनुरोध संपादित करें",
        "confirm_go": "पुष्टि करें और मार्ग खोजें",
        "results_title": "सर्वोत्तम अगला कदम",
        "scale": {
            "Routine": "सामान्य", "Soon": "जल्द", "Urgent": "तत्काल",
            "Low": "कम", "Medium": "मध्यम", "High": "अधिक",
            "Either": "कोई भी", "Public": "सरकारी", "Private": "निजी",
        },
    },
    "mr": {
        "hero_tagline": "योग्य काळजी मार्ग — <em>पुराव्यासह.</em>",
        "hero_sub": "तुमची गरज सोप्या शब्दांत सांगा. Aven पुढील पाऊल ठरवते आणि त्यामागील पुरावा दाखवते.",
        "scroll_cue": "खाली पहा",
        "nav_cta": "पहा",
        "marquee": [
            "योग्य मार्ग, स्पष्टपणे",
            "काळजी, पुराव्यासह",
            "अनिश्चिततेबद्दल प्रामाणिक",
            "पुरावा जो तुम्ही पाहू शकता",
        ],
        "statement_kicker": "कल्पना",
        "statement": (
            'काळजीची गरज बनते <span class="dim">एक स्पष्ट विनंती, एक कृतीयोग्य मार्ग,</span> '
            'आणि प्रत्येक पर्यायामागील पुरावा.'
        ),
        "about_eyebrow": "हे कसे कार्य करते",
        "about_title": "काळजी, जी पुराव्यासह येते.",
        "about_body": (
            "काळजी मिळवण्याची तुमची गरज सोप्या शब्दांत सांगा. Aven ती स्पष्ट, संरचित विनंतीमध्ये "
            "बदलते, नंतर कृतीयोग्य मार्ग ठरवते — प्रत्येक पर्यायामागील पुरावा दाखवत आणि ज्याची "
            "पुष्टी होऊ शकली नाही त्याबद्दल प्रामाणिक राहत."
        ),
        "about_points": [
            ("तुमच्या शब्दांत सांगा", "इंग्रजी, हिंदी किंवा मराठीत सहजपणे लिहा. गुंतागुंतीचे फॉर्म नाहीत."),
            ("पुरावा पहा", "प्रत्येक पर्याय दाखवतो काय नोंदवलेले आहे, काय विसंगत आहे आणि काय अज्ञात आहे."),
            ("पुढील पाऊल ठरवा", "प्रवास आणि खर्चानुसार मार्गांची तुलना करा, नंतर योजना जतन करा."),
        ],
        "tiles_eyebrow": "सुरुवात निवडा",
        "tiles_title": "आज तुम्हाला काय हवे आहे?",
        "tiles_hint": "प्रत्येक पर्याय स्वतःचा फॉर्म उघडतो — तुम्ही कधीही बदलू शकता.",
        "switcher_label": "तुमच्या गरजेसाठी फॉर्म निवडा",
        "specifics": "तपशील",
        "location_label": "तुम्ही कुठून सुरुवात करत आहात?",
        "location_ph": "शहर, जिल्हा किंवा पिनकोड",
        "extra_label": "आणखी काही आम्हाला माहीत असावे? (ऐच्छिक)",
        "extra_ph": "उदाहरण: डॉक्टरांनी हृदयरोग तज्ज्ञांकडे जाण्यास सांगितले आहे आणि मी दूर प्रवास करू शकत नाही.",
        "prefs": "तुमच्या पसंती",
        "prefs_why": "आम्ही हे का विचारतो? प्रवास आणि बजेट पसंती मार्गांचा क्रम बदलतात, काळजीची गुणवत्ता नाही.",
        "urgency_label": "तुम्हाला किती लवकर कृती करायची आहे?",
        "travel_label": "तुम्ही किती दूर प्रवास करू शकता?",
        "budget_label": "खर्च कमी करणे किती महत्त्वाचे आहे?",
        "facility_label": "सुविधा पसंती",
        "language_label": "पसंतीची भाषा (ऐच्छिक)",
        "submit": "Aven ने काय समजले ते पहा",
        "confirm_title": "नियोजनापूर्वी पुष्टी करा",
        "confirm_edit": "विनंती संपादित करा",
        "confirm_go": "पुष्टी करा आणि मार्ग शोधा",
        "results_title": "सर्वोत्तम पुढील पाऊल",
        "scale": {
            "Routine": "नियमित", "Soon": "लवकर", "Urgent": "तातडीचे",
            "Low": "कमी", "Medium": "मध्यम", "High": "जास्त",
            "Either": "कोणतेही", "Public": "सरकारी", "Private": "खाजगी",
        },
    },
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
        "switcher_label": "Choose the form for your need",
        "specifics": "The specifics",
        "location_label": "Where are you starting from?",
        "location_ph": "City, district, or pincode",
        "extra_label": "Anything else we should know? (optional)",
        "extra_ph": "Example: My doctor said I need a cardiology visit and I cannot travel far.",
        "prefs": "Your preferences",
        "prefs_why": "Why do we ask this? Travel and budget preferences change route ordering, not care quality.",
        "urgency_label": "How soon do you need to act?",
        "travel_label": "How far can you travel?",
        "budget_label": "How important is minimizing cost?",
        "facility_label": "Facility preference",
        "language_label": "Preferred language (optional)",
        "submit": "Review what Aven understood",
        "confirm_title": "Please confirm before we plan",
        "confirm_edit": "Edit request",
        "confirm_go": "Confirm and find routes",
        "results_title": "Best next step",
        # Identity map: scale() falls back to the English value, which is also the
        # canonical value stored on the request.
        "scale": {},
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
    {"key": "vaccination", "icon": "💉", "title": "Vaccination",
     "desc": "Find where to get a vaccine or routine immunization.",
     "detail_label": "Which vaccine or immunization are you planning for?"},
    {"key": "follow_up", "icon": "📅", "title": "Follow-up question",
     "desc": "Reconnect with a facility or doctor about an appointment.",
     "detail_label": "Which facility or doctor are you trying to reach?"},
    {"key": "symptom_first", "icon": "🧭", "title": "Not sure what I need",
     "desc": "Talk it through and plan a safe next step. This is not a diagnosis.",
     "detail_label": "What is worrying you today?"},
]

TASK_META = {tile["key"]: tile for tile in FEATURE_TILES}

# Per-language tile copy, keyed by care task. Icons and keys stay in FEATURE_TILES
# because they are not language-dependent — only title/desc/detail_label are.
TILE_COPY = {
    "hi": {
        "known_referral": ("रेफरल या प्रक्रिया",
                           "डॉक्टर द्वारा बताई गई विशेषज्ञ जांच या प्रक्रिया के लिए मार्ग बनाएं।",
                           "आपके डॉक्टर ने किसके लिए रेफर किया?"),
        "refill": ("दवा दोबारा लेना",
                   "पर्चा दोबारा भरवाने या दवा की दुकान तक पहुंचने की जगह खोजें।",
                   "आपको कौन सी दवा दोबारा चाहिए?"),
        "lab": ("लैब या रक्त जांच",
                "चिकित्सक द्वारा बताई गई जांच या रक्त नमूने के लिए सुविधा खोजें।",
                "कौन सी जांच या रक्त नमूना बताया गया?"),
        "vaccination": ("टीकाकरण",
                        "टीका या नियमित प्रतिरक्षण कहां मिलेगा, यह खोजें।",
                        "आप किस टीके या प्रतिरक्षण की योजना बना रहे हैं?"),
        "follow_up": ("अनुवर्ती प्रश्न",
                      "अपॉइंटमेंट के बारे में सुविधा या डॉक्टर से दोबारा संपर्क करें।",
                      "आप किस सुविधा या डॉक्टर तक पहुंचना चाहते हैं?"),
        "symptom_first": ("मुझे नहीं पता क्या चाहिए",
                          "बात करें और सुरक्षित अगला कदम तय करें। यह निदान नहीं है।",
                          "आज आपको क्या चिंता है?"),
    },
    "mr": {
        "known_referral": ("संदर्भ किंवा प्रक्रिया",
                           "डॉक्टरांनी सुचवलेल्या तज्ज्ञ भेटीसाठी किंवा प्रक्रियेसाठी मार्ग ठरवा.",
                           "तुमच्या डॉक्टरांनी कशासाठी संदर्भ दिला?"),
        "refill": ("औषध पुन्हा घेणे",
                   "प्रिस्क्रिप्शन पुन्हा भरण्यासाठी किंवा औषधालयापर्यंत पोहोचण्यासाठी जागा शोधा.",
                   "तुम्हाला कोणते औषध पुन्हा हवे आहे?"),
        "lab": ("प्रयोगशाळा किंवा रक्त तपासणी",
                "डॉक्टरांनी सांगितलेल्या तपासणीसाठी किंवा रक्त नमुन्यासाठी सुविधा शोधा.",
                "कोणती तपासणी किंवा रक्त नमुना सांगितला होता?"),
        "vaccination": ("लसीकरण",
                        "लस किंवा नियमित लसीकरण कुठे मिळेल ते शोधा.",
                        "तुम्ही कोणत्या लसीचे नियोजन करत आहात?"),
        "follow_up": ("पाठपुरावा प्रश्न",
                      "अपॉइंटमेंटबद्दल सुविधा किंवा डॉक्टरांशी पुन्हा संपर्क साधा.",
                      "तुम्ही कोणत्या सुविधेशी किंवा डॉक्टरांशी संपर्क साधू इच्छिता?"),
        "symptom_first": ("मला काय हवे ते माहीत नाही",
                          "चर्चा करा आणि सुरक्षित पुढील पाऊल ठरवा. हे निदान नाही.",
                          "आज तुम्हाला कशाची चिंता आहे?"),
    },
}


def ui_language() -> str:
    return st.session_state.get("language", "en")


def t() -> dict:
    return STRINGS[ui_language()]


def tx(key: str) -> object:
    """UI copy lookup with per-key English fallback for untranslated keys."""
    return UI_COPY.get(ui_language(), {}).get(key, UI_COPY["en"][key])


def scale_labels():
    """Return a format_func that labels canonical option values in the current
    language. The language is bound now rather than read on each call, so the
    function stays pure once built — Streamlit and its test harness both invoke
    format_func outside the render context, where ambient state is unreliable.

    Option *values* are never translated: they are what the request stores and
    what domain validation reads.
    """
    table = UI_COPY.get(ui_language(), {}).get("scale", {})
    return lambda value: table.get(value, value)


def tile_copy(care_task: str) -> dict:
    """Tile title/desc/detail_label in the current language, falling back to the
    English text authored on FEATURE_TILES."""
    meta = TASK_META[care_task]
    translated = TILE_COPY.get(ui_language(), {}).get(care_task)
    if not translated:
        return meta
    title, desc, detail_label = translated
    return {**meta, "title": title, "desc": desc, "detail_label": detail_label}


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
        "language_notice": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def ui_backend() -> AvenUiBackend:
    """The shared UI façade (src/ui_contract.py). Cheap to build — it only seeds
    two session keys — so views can just call it. Status, travel truth, and
    approved copy come from here rather than being reimplemented in the view.

    Planning still goes through backend.service: the façade's confirm_and_plan is
    demo-only and would drop the live Databricks path. That seam is unresolved —
    see apps/TODO.md.
    """
    return AvenUiBackend(st.session_state)


def apply_language_param() -> None:
    """Honor `?lang=` but degrade visibly. resolve_language accepts codes, locale
    variants, and native names; anything else falls back to English *with a
    message* rather than silently rendering the wrong language."""
    requested = st.query_params.get("lang")
    if not requested or st.session_state.get("language_param_seen") == requested:
        return
    st.session_state.language_param_seen = requested
    selection = resolve_language(requested)
    st.session_state.language = selection.code
    st.session_state.language_notice = selection.fallback_message


# ---------- Profile helpers ----------

def current_profile() -> dict:
    return st.session_state.profile


def is_logged_in() -> bool:
    return st.session_state.user is not None


def persist_profile() -> None:
    """Persist via the Lakebase seam (local JSON fallback today). Logged-in only;
    guests stay session-only."""
    if is_logged_in():
        backend.save_profile(st.session_state.profile)


def do_login(name: str, email: str) -> None:
    email = email.strip()
    profile = backend.load_profile(email)
    if name.strip():
        profile["name"] = name.strip()
    st.session_state.profile = profile
    st.session_state.user = {"name": profile.get("name") or "Member", "email": email}
    backend.save_profile(profile)
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
                # An explicit choice supersedes any ?lang= fallback notice.
                st.session_state.language_notice = None
                st.rerun()
        idx += 1
        with cols[idx]:
            show_account_control()

    # Rendered outside the sticky container so it reads as a page-level notice.
    if st.session_state.get("language_notice"):
        st.info(st.session_state.language_notice)


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

    # Six forms render as a neat 3-wide grid (two rows). Each button's parent
    # gets a `st-key-tile_*` class from Streamlit, which the CSS targets to style
    # the button as a large, hoverable card while keeping full session state.
    # (Saved plans are reachable from the header and profile, not this grid.)
    for row_start in range(0, len(FEATURE_TILES), 3):
        row = [tile_copy(t["key"]) for t in FEATURE_TILES[row_start:row_start + 3]]
        cols = st.columns(3)
        for col, tile in zip(cols, row):
            label = f"{tile['icon']}\n\n**{tile['title']}**\n\n{tile['desc']}\n\n{tx('nav_cta')} →"
            if col.button(label, key=f"tile_{tile['key']}", use_container_width=True):
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
    st.markdown(f'<div class="aven-switcher-label">{tx("switcher_label")}</div>', unsafe_allow_html=True)
    cols = st.columns(len(FEATURE_TILES))
    for col, tile in zip(cols, (tile_copy(t["key"]) for t in FEATURE_TILES)):
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
    meta = tile_copy(care_task)

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

    # Say plainly whether voice input is available instead of leaving its absence
    # to be discovered. Typed input is always the supported path.
    st.caption(f"🎤 {ui_backend().service_status()['voice_message']}")

    st.markdown('<div class="aven-reveal">', unsafe_allow_html=True)
    with st.form("intake_form"):
        st.markdown(f'<div class="aven-section-title">{tx("specifics")}</div>', unsafe_allow_html=True)
        detail = st.text_input(meta["detail_label"], placeholder=next_question(care_task))
        location = st.text_input(tx("location_label"), placeholder=tx("location_ph"))
        message = st.text_area(tx("extra_label"), placeholder=tx("extra_ph"))

        st.markdown(f'<div class="aven-section-title">{tx("prefs")}</div>', unsafe_allow_html=True)
        st.caption(tx("prefs_why"))
        pref_left, pref_right = st.columns(2)
        # Option values stay English: they are stored on the request and validated
        # by the domain. Only their displayed labels are localized, so switching
        # language mid-form relabels the controls without invalidating the answers.
        label_for = scale_labels()
        with pref_left:
            urgency = st.select_slider(tx("urgency_label"), options=["Routine", "Soon", "Urgent"],
                                       value="Soon", format_func=label_for)
            travel = st.select_slider(tx("travel_label"), options=["Low", "Medium", "High"],
                                      value="Medium", format_func=label_for)
        with pref_right:
            budget = st.select_slider(tx("budget_label"), options=["Low", "Medium", "High"],
                                      value="High", format_func=label_for)
            preference = st.radio(tx("facility_label"), options=["Either", "Public", "Private"],
                                  horizontal=True, format_func=label_for)
        language = st.text_input(tx("language_label"))
        submitted = st.form_submit_button(tx("submit"), type="primary", use_container_width=True)
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
    st.markdown(f'<div class="aven-section-title">{tx("confirm_title")}</div>', unsafe_allow_html=True)
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
        if st.button(tx("confirm_edit"), use_container_width=True):
            st.session_state.stage = "intake"
            st.rerun()
    with right:
        if st.button(tx("confirm_go"), type="primary", use_container_width=True):
            st.session_state.options = backend.plan_routes(request)
            profiles.add_history(current_profile(), request)
            persist_profile()
            st.session_state.stage = "results"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_enrichment(option: dict) -> None:
    """Render the extractor's per-facility output schema: what was documented,
    with the literal span behind each claim, and what the record itself is not
    trustworthy about. Nothing here is inferred — an empty section is stated as a
    gap in the record, never as an absent service."""
    data = enrich.normalize(option.get("enrichment"))

    st.markdown(chips_html(data["specialties"]), unsafe_allow_html=True)
    for line in enrich.cautions(data):
        sparse = line.startswith("This facility's record is sparse")
        st.markdown(quality_note_html(line, sparse=sparse), unsafe_allow_html=True)

    if enrich.is_empty(data):
        st.caption("Nothing could be extracted from this facility's record yet. Confirm services by phone.")
        return

    unverified = enrich.unverified_count(data)
    summary = "What the records say"
    if unverified:
        summary += f" · {unverified} claim(s) without a source span"
    with st.expander(summary):
        current_heading = None
        for heading, text, evidence, verified in enrich.iter_claims(data):
            if heading != current_heading:
                st.markdown(f'<div class="aven-claim-group">{heading}</div>', unsafe_allow_html=True)
                current_heading = heading
            st.markdown(claim_html(text, evidence, verified), unsafe_allow_html=True)

        conflicts = data["data_quality"]["conflicting_claims"]
        if conflicts:
            st.markdown('<div class="aven-claim-group">Conflicting details</div>', unsafe_allow_html=True)
            for conflict in conflicts:
                st.markdown(claim_html(conflict, [], True), unsafe_allow_html=True)


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

        show_enrichment(option)

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


# Modes worth stating truth about for care access. Every one is validated by
# maps.validate_travel_mode inside the façade, so an unsupported mode raises here
# rather than reaching the user as a fake capability.
TRAVEL_MODES = ("walk", "bus", "train", "car", "taxi")


def show_system_status() -> None:
    """What is actually connected right now. Capability state only — the façade
    deliberately exposes no credentials or endpoint identifiers."""
    status = ui_backend().service_status()
    rows = [
        ("Evidence pipeline", "Live Databricks evidence" if backend.backend_mode() == "live"
         else "Seeded demo data — Vector Search and Agent Bricks are not connected"),
        ("Routing provider", f"{status['map_provider']}"
         + (" (live)" if status["map_live_provider"] else " (offline estimates only)")),
        ("Facility database", f"Databricks SQL {status['databricks_mode']}"),
        ("Voice input", status["voice_message"]),
    ]
    with st.expander("What is connected right now"):
        for label, value in rows:
            st.markdown(f'<p class="aven-fact"><strong>{label}:</strong> {value}</p>', unsafe_allow_html=True)


def show_travel_truth() -> None:
    """State per-mode what the routing provider can and cannot answer, so a travel
    estimate is never mistaken for a live route, fare, or transit status."""
    capabilities = ui_backend().travel_capabilities(TRAVEL_MODES)
    with st.expander("What we can and cannot tell you about travel"):
        st.caption(
            "Travel figures above are estimates for comparison. None of them is a live "
            "route, a fare quote, or confirmation that a service is running."
        )
        for row in capabilities:
            st.markdown(
                f'<p class="aven-fact"><strong>{row["mode"].title()}:</strong> {row["label"]}</p>',
                unsafe_allow_html=True,
            )


def show_results() -> None:
    request = st.session_state.request
    st.markdown(f'<div class="aven-section-title">{tx("results_title")}</div>', unsafe_allow_html=True)
    st.caption(f"For: {request['capability']} · Starting from: {request['location']}")

    if backend.backend_mode() == "demo":
        st.markdown(
            '<div class="aven-datasource-note">⚙️ Seeded demo data — the Databricks evidence pipeline '
            '(Vector Search · Agent Bricks · Lakebase) is not connected in this environment. '
            'Every option is labelled as a demo.</div>',
            unsafe_allow_html=True,
        )

    show_system_status()

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

    if visible:
        show_travel_truth()

    st.markdown('<div class="aven-reveal">', unsafe_allow_html=True)
    st.markdown('<div class="aven-section-title">Was this plan useful?</div>', unsafe_allow_html=True)
    label = st.selectbox("What happened?", options=list(FEEDBACK_OPTIONS))
    note = st.text_input("Optional correction or note")
    if st.button("Save feedback"):
        st.session_state.feedback = {"status": FEEDBACK_OPTIONS[label], "note": note}
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
    apply_language_param()

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
        f"</div>",
        unsafe_allow_html=True,
    )
    # Injected last so every .aven-reveal element above already exists in the
    # DOM by the time this script runs and starts observing them.
    components.html(SCROLL_REVEAL_JS, height=0)


if __name__ == "__main__":
    main()
