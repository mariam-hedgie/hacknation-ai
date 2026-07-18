"""Shared visual system for the Aven Streamlit UI.

Centralizes the calm, accessible design language from docs/ui-handoff.md so
screens stay visually consistent: color, spacing, evidence-status badges, and
touch-target sizing. No clinical or ranking logic lives here.
"""

from __future__ import annotations

CSS = """
<style>
:root {
  --aven-ink: #1c2430;
  --aven-muted: #5b6472;
  --aven-bg: #f7f8fa;
  --aven-card: #ffffff;
  --aven-border: #e2e6ec;
  --aven-primary: #0f6e6a;
  --aven-primary-ink: #ffffff;
  --aven-documented-bg: #e6f4f3;
  --aven-documented-ink: #0f6e6a;
  --aven-conflict-bg: #fdf1de;
  --aven-conflict-ink: #8a5a06;
  --aven-unknown-bg: #eef0f3;
  --aven-unknown-ink: #4b5563;
  --aven-external-bg: #eaf0fb;
  --aven-external-ink: #2451a3;
  --aven-user-bg: #f5f0fb;
  --aven-user-ink: #6a3fa0;
  --aven-emergency-bg: #fdeceb;
  --aven-emergency-border: #d64545;
  --aven-emergency-ink: #7a1f1f;
}

@media (prefers-color-scheme: dark) {
  :root {
    --aven-ink: #eef1f5;
    --aven-muted: #aab2bf;
    --aven-bg: #10151b;
    --aven-card: #182029;
    --aven-border: #2a3340;
    --aven-primary: #35a79f;
    --aven-primary-ink: #06201d;
    --aven-documented-bg: #103330;
    --aven-documented-ink: #6cd6cc;
    --aven-conflict-bg: #3a2a10;
    --aven-conflict-ink: #f0b955;
    --aven-unknown-bg: #232a33;
    --aven-unknown-ink: #c3c9d1;
    --aven-external-bg: #182338;
    --aven-external-ink: #8fb3f0;
    --aven-user-bg: #241c33;
    --aven-user-ink: #c6a6f0;
    --aven-emergency-bg: #3a1414;
    --aven-emergency-border: #e06868;
    --aven-emergency-ink: #f5b6b6;
  }
}

.stApp { background: var(--aven-bg); }
.block-container { padding-top: 1.5rem; max-width: 760px; }

.aven-header { display: flex; align-items: baseline; gap: 0.6rem; flex-wrap: wrap; }
.aven-title { font-size: 1.9rem; font-weight: 700; color: var(--aven-ink); margin: 0; }
.aven-tagline { color: var(--aven-muted); font-size: 1rem; }

.aven-stepper { display: flex; gap: 0.5rem; margin: 0.9rem 0 1.2rem 0; }
.aven-step {
  flex: 1; text-align: center; padding: 0.5rem 0.4rem; border-radius: 10px;
  font-size: 0.85rem; font-weight: 600; color: var(--aven-muted);
  background: var(--aven-card); border: 1px solid var(--aven-border);
}
.aven-step.active { color: var(--aven-primary-ink); background: var(--aven-primary); border-color: var(--aven-primary); }
.aven-step.done { color: var(--aven-primary); border-color: var(--aven-primary); }

.aven-boundary {
  background: var(--aven-card); border: 1px solid var(--aven-border); border-radius: 10px;
  padding: 0.7rem 0.9rem; color: var(--aven-muted); font-size: 0.88rem; margin-bottom: 1rem;
}

.aven-card {
  background: var(--aven-card); border: 1px solid var(--aven-border); border-radius: 14px;
  padding: 1.1rem 1.2rem; margin-bottom: 1rem;
}

.aven-badge {
  display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.28rem 0.65rem;
  border-radius: 999px; font-size: 0.82rem; font-weight: 600; white-space: nowrap;
}
.aven-badge.documented { background: var(--aven-documented-bg); color: var(--aven-documented-ink); }
.aven-badge.conflicting { background: var(--aven-conflict-bg); color: var(--aven-conflict-ink); }
.aven-badge.not_documented { background: var(--aven-unknown-bg); color: var(--aven-unknown-ink); }
.aven-badge.external_corroborated { background: var(--aven-external-bg); color: var(--aven-external-ink); }
.aven-badge.user_context { background: var(--aven-user-bg); color: var(--aven-user-ink); border: 1px dashed var(--aven-user-ink); }

.aven-option-label {
  font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
  color: var(--aven-primary); margin-bottom: 0.15rem;
}
.aven-facility-name { font-size: 1.25rem; font-weight: 700; color: var(--aven-ink); margin: 0 0 0.3rem 0; }
.aven-fact { color: var(--aven-ink); font-size: 0.92rem; margin: 0.15rem 0; }
.aven-fact strong { color: var(--aven-ink); }

.aven-emergency {
  background: var(--aven-emergency-bg); border: 2px solid var(--aven-emergency-border);
  color: var(--aven-emergency-ink); border-radius: 14px; padding: 1.2rem 1.3rem; margin-bottom: 1rem;
}
.aven-emergency h3 { margin-top: 0; color: var(--aven-emergency-ink); }

.aven-chip-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.4rem 0 0.8rem 0; }

/* Touch targets and focus visibility */
.stButton > button, .stRadio, .stSelectbox, .stTextInput input, .stTextArea textarea {
  min-height: 44px;
}
.stButton > button {
  border-radius: 10px !important;
  font-weight: 600 !important;
}
:focus-visible { outline: 3px solid var(--aven-primary) !important; outline-offset: 2px; }

.aven-footer-note { color: var(--aven-muted); font-size: 0.8rem; margin-top: 1.5rem; text-align: center; }
</style>
"""

EVIDENCE_BADGES: dict[str, tuple[str, str]] = {
    "documented": ("check", "Documented in facility records"),
    "conflicting": ("alert", "Details disagree — call first"),
    "not_documented": ("question", "We could not confirm this"),
    "external_corroborated": ("link", "Official external source"),
    "user_context": ("note", "You told us this"),
}

_ICONS = {"check": "✅", "alert": "⚠️", "question": "❔", "link": "🔗", "note": "🗒️"}


def evidence_badge_html(status: str) -> str:
    icon_key, copy = EVIDENCE_BADGES.get(status, EVIDENCE_BADGES["not_documented"])
    icon = _ICONS[icon_key]
    return f'<span class="aven-badge {status}">{icon} {copy}</span>'
