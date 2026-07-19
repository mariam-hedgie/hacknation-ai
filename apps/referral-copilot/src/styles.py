"""Shared visual system for the Aven Streamlit UI.

A light, editorial design language: near-black type on warm paper, one teal
accent, oversized display headings, thin hairline rules, a scrolling marquee,
and generous whitespace. The hospital identity survives only as a subtle cue —
a thin ECG hairline used as a divider and a heartbeat glyph in the wordmark.
No clinical or ranking logic lives here.
"""

from __future__ import annotations

FONT_IMPORT = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800'
    "&family=Manrope:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\">"
)

CSS = """
<style>
:root {
  --ink: #17160f;
  --muted: #6c6a5f;
  --faint: #9a978b;
  --paper: #f4f2ec;
  --paper-2: #efece4;
  --card: #fbfaf5;
  --line: #ddd9cf;
  --line-strong: #cbc7ba;
  --accent: #0f6e6a;
  --accent-deep: #0b5652;
  --accent-soft: #e7f1ef;
  --documented-bg: #e7f1ef; --documented-ink: #0f6e6a;
  --conflict-bg: #f6ecd8;  --conflict-ink: #8a5a06;
  --unknown-bg: #ecebe4;   --unknown-ink: #55534a;
  --external-bg: #e7ecf6;  --external-ink: #2451a3;
  --user-bg: #efe9f6;      --user-ink: #6a3fa0;
  --emergency-bg: #f8e7e3; --emergency-border: #c6503f; --emergency-ink: #7a1f1f;
  --shadow: rgba(23, 22, 15, 0.12);
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #efece4;
    --muted: #a29e92;
    --faint: #726e63;
    --paper: #12110d;
    --paper-2: #16150f;
    --card: #1a1811;
    --line: #2c2a22;
    --line-strong: #3a3830;
    --accent: #2bb3a8;
    --accent-deep: #6cd6cc;
    --accent-soft: #14261f;
    --documented-bg: #12261f; --documented-ink: #6cd6cc;
    --conflict-bg: #2c2210;  --conflict-ink: #e6b24e;
    --unknown-bg: #23221b;   --unknown-ink: #bdbaad;
    --external-bg: #16203a;  --external-ink: #8fb3f0;
    --user-bg: #201a2e;      --user-ink: #c6a6f0;
    --emergency-bg: #2c1512; --emergency-border: #d9695a; --emergency-ink: #f0b5ac;
    --shadow: rgba(0, 0, 0, 0.5);
  }
}

html { scroll-behavior: smooth; }
html, body, [class*="css"] { font-family: 'Manrope', -apple-system, sans-serif; color: var(--ink); }
/* `clip` prevents the full-bleed 100vw sections from creating a horizontal
   scrollbar without turning .stApp into a scroll container (which would break
   the sticky header's positioning). */
.stApp { background: var(--paper); overflow-x: clip; }

.aven-display, .aven-title, .aven-nav-brand span, .aven-statement-text, .aven-about-title,
.aven-form-title, .aven-facility-name {
  font-family: 'Bricolage Grotesque', 'Manrope', sans-serif;
}

/* Hide Streamlit's default top chrome; the custom header owns the top edge. */
header[data-testid="stHeader"] { display: none; }
/* Leave room for the fixed header (~3.4rem tall) so content never hides beneath it. */
.block-container { padding-top: 3.4rem; padding-bottom: 4rem; max-width: 940px; }
[id^="aven-"] { scroll-margin-top: 5rem; }

/* ---------- Eyebrow / kicker ---------- */
.aven-eyebrow {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.24em; text-transform: uppercase;
  color: var(--accent); display: inline-flex; align-items: center; gap: 0.5rem;
}

/* ---------- Sticky interactive header (Streamlit widgets) ----------
   The header row is a keyed container (st-key-aven_header). It is made sticky
   and full-bleed here; the buttons and language picker inside it are restyled
   into minimal nav links. */
.st-key-aven_header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  padding: 0.3rem clamp(1rem, 5vw, 2.4rem);
  background: color-mix(in srgb, var(--paper) 92%, transparent);
  backdrop-filter: saturate(140%) blur(14px); -webkit-backdrop-filter: saturate(140%) blur(14px);
  border-bottom: 1px solid var(--line);
}
.st-key-aven_header [data-testid="stHorizontalBlock"] { max-width: 1120px; margin: 0 auto; align-items: center; }
.st-key-aven_header [data-testid="stVerticalBlock"] { gap: 0; }

/* Base: strip Streamlit chrome off every control in the header. */
.st-key-aven_header .stButton > button,
.st-key-aven_header [data-testid="stPopover"] button {
  border: none !important; background: transparent !important; color: var(--ink) !important;
  border-radius: 999px !important; min-height: 40px !important;
  font-size: 0.74rem !important; font-weight: 700 !important; letter-spacing: 0.12em; text-transform: uppercase;
  transition: color 0.15s ease, background 0.15s ease !important; box-shadow: none !important;
}
.st-key-aven_header .stButton > button:hover,
.st-key-aven_header [data-testid="stPopover"] button:hover {
  background: var(--accent-soft) !important; color: var(--accent) !important; transform: none !important;
}
/* The brand button: bigger, tighter, the wordmark. */
.st-key-brand_home button {
  font-family: 'Bricolage Grotesque', sans-serif !important;
  font-size: 1.35rem !important; font-weight: 800 !important; letter-spacing: -0.01em !important;
  text-transform: uppercase; padding-left: 0 !important; justify-content: flex-start !important;
}
.st-key-brand_home button:hover { background: transparent !important; color: var(--accent) !important; }

/* Language picker in the header: compact, borderless. */
.st-key-lang_header div[data-baseweb="select"] > div {
  border: 1px solid var(--line-strong) !important; background: transparent !important;
  min-height: 40px; border-radius: 999px !important;
}
.st-key-lang_header { display: flex; justify-content: flex-end; }

/* Forms dropdown panel content. */
[data-testid="stPopoverBody"] .stButton > button {
  border: 1px solid var(--line) !important; background: var(--card) !important; color: var(--ink) !important;
  border-radius: 8px !important; text-align: left !important; justify-content: flex-start !important;
  text-transform: none !important; letter-spacing: 0 !important; font-weight: 600 !important;
}
[data-testid="stPopoverBody"] .stButton > button:hover {
  background: var(--ink) !important; color: var(--paper) !important; border-color: var(--ink) !important;
}

/* ---------- Heartbeat glyph (subtle medical cue) ---------- */
.aven-logo-pulse path {
  fill: none; stroke: var(--accent); stroke-width: 3.4; stroke-linecap: round; stroke-linejoin: round;
  transform-origin: center; animation: aven-heartbeat 2.8s ease-in-out infinite;
}
@keyframes aven-heartbeat {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  22% { transform: scale(1.09); opacity: 1; }
  34% { transform: scale(0.99); }
  46% { transform: scale(1.13); opacity: 1; }
  62% { transform: scale(1); opacity: 0.85; }
}

/* ---------- Full-bleed editorial hero ---------- */
.aven-hero-full {
  width: 100vw; margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw);
  margin-top: -3.4rem; margin-bottom: 0;
  min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;
  padding: 6rem clamp(1.5rem, 6vw, 5rem) 4rem; text-align: center;
  border-bottom: 1px solid var(--line);
  background:
    radial-gradient(60% 50% at 50% 0%, var(--accent-soft) 0%, transparent 70%),
    var(--paper);
}
.aven-hero-inner { max-width: 1100px; display: flex; flex-direction: column; align-items: center; gap: 1.1rem; }
.aven-display {
  margin: 0.3rem 0 0 0; color: var(--ink); text-transform: uppercase;
  font-size: clamp(5rem, 24vw, 20rem); font-weight: 800; letter-spacing: -0.05em; line-height: 0.84;
}
.aven-hero-tagline {
  font-size: clamp(1.3rem, 3.4vw, 2.2rem); font-weight: 500; color: var(--ink); line-height: 1.15;
  max-width: 22ch; margin: 0.2rem 0 0 0; letter-spacing: -0.01em;
}
.aven-hero-tagline em { font-style: italic; color: var(--accent); }
.aven-hero-sub { color: var(--muted); font-size: 1.02rem; max-width: 46ch; margin: 0; }
.aven-scroll-cue {
  margin-top: 1.4rem; display: inline-flex; flex-direction: column; align-items: center; gap: 0.15rem;
  text-decoration: none; color: var(--faint);
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase;
}
.aven-scroll-cue .aven-chevron { font-size: 1.4rem; line-height: 1; animation: aven-bounce 1.9s ease-in-out infinite; }
.aven-scroll-cue:hover { color: var(--accent); }
@keyframes aven-bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(6px); } }

/* ---------- ECG hairline divider ---------- */
.aven-ecg-divider {
  width: min(340px, 60%); height: 22px; display: block; margin: 0.4rem auto 0;
}
.aven-ecg-divider path {
  fill: none; stroke: var(--accent); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; opacity: 0.85;
}
.aven-ecg-divider .aven-ecg-blip { animation: aven-blip 2.8s ease-in-out infinite; transform-origin: center; }
@keyframes aven-blip { 0%,100% { opacity: 0.85; } 50% { opacity: 0.35; } }

/* ---------- Marquee ticker (Longbow signature) ---------- */
.aven-marquee {
  width: 100vw; margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw);
  overflow: hidden; border-bottom: 1px solid var(--line);
  background: var(--ink); color: var(--paper); padding: 0.9rem 0;
}
.aven-marquee-track {
  display: inline-flex; white-space: nowrap; will-change: transform;
  animation: aven-marquee 26s linear infinite;
}
.aven-marquee-track span {
  font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; text-transform: uppercase;
  font-size: clamp(1rem, 2.2vw, 1.5rem); letter-spacing: 0.02em; padding: 0 1.4rem;
  display: inline-flex; align-items: center; gap: 1.4rem;
}
.aven-marquee-track span::after { content: "✦"; color: var(--accent-deep); font-size: 0.8em; }
@keyframes aven-marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.aven-marquee:hover .aven-marquee-track { animation-play-state: paused; }

/* ---------- Big statement section ---------- */
.aven-statement { margin: 4.5rem 0; }
.aven-statement-text {
  font-size: clamp(1.6rem, 4.2vw, 3rem); font-weight: 600; line-height: 1.15; letter-spacing: -0.02em;
  color: var(--ink); max-width: 20ch; margin: 0.6rem 0 0 0;
}
.aven-statement-text .dim { color: var(--faint); }

/* ---------- Section title (small kicker) ---------- */
.aven-section-title {
  font-size: 0.74rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--muted); margin: 0; display: inline-flex; align-items: center; gap: 0.6rem;
}
.aven-section-title::before { content: ""; width: 26px; height: 1px; background: var(--accent); }

/* ---------- Numbered principles ---------- */
.aven-about { margin: 4.5rem 0 3rem; }
.aven-about-title {
  font-size: clamp(1.9rem, 5vw, 3rem); font-weight: 800; color: var(--ink);
  letter-spacing: -0.03em; line-height: 1.02; margin: 0.6rem 0 0.6rem 0;
}
.aven-about-body { color: var(--muted); font-size: 1.05rem; line-height: 1.6; max-width: 52ch; }
.aven-about-points { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; margin-top: 2.4rem; }
.aven-about-point {
  padding: 1.6rem 1.5rem 1.6rem 0; border-top: 1px solid var(--line-strong);
}
.aven-about-point:not(:last-child) { border-right: 1px solid var(--line); padding-right: 1.5rem; }
.aven-about-point:not(:first-child) { padding-left: 1.5rem; }
.aven-about-point-num {
  font-family: 'Bricolage Grotesque', sans-serif; font-size: 0.9rem; font-weight: 700;
  color: var(--accent); margin-bottom: 0.7rem; letter-spacing: 0.05em;
}
.aven-about-point h4 { margin: 0 0 0.4rem 0; font-size: 1.1rem; font-weight: 700; color: var(--ink); }
.aven-about-point p { margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.5; }

/* ---------- Tiles (the "forms") ---------- */
.aven-tiles-head { margin: 4rem 0 1.6rem 0; }
.aven-tiles-hint { color: var(--muted); font-size: 1rem; margin: 0.4rem 0 0 0; }

div[class*="st-key-tile_"] button {
  min-height: 214px; height: 100%; text-align: left !important;
  display: flex; flex-direction: column; align-items: flex-start !important; justify-content: flex-start;
  gap: 0.1rem; padding: 1.4rem 1.5rem 1.5rem !important; border-radius: 14px !important;
  background: var(--card) !important; border: 1px solid var(--line-strong) !important;
  box-shadow: 0 1px 2px rgba(23,22,15,0.04) !important; cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease !important;
  position: relative; overflow: hidden;
}
/* A persistent corner marker so the card reads as clickable at rest. */
div[class*="st-key-tile_"] button::before {
  content: "↗"; position: absolute; top: 1.1rem; right: 1.3rem;
  width: 30px; height: 30px; border-radius: 999px; border: 1px solid var(--line-strong);
  display: flex; align-items: center; justify-content: center;
  color: var(--accent); font-size: 1rem; transition: all 0.22s ease;
}
div[class*="st-key-tile_"] button:hover {
  background: var(--ink) !important; border-color: var(--ink) !important; transform: translateY(-4px) !important;
  box-shadow: 0 24px 40px -26px var(--shadow) !important;
}
div[class*="st-key-tile_"] button:hover::before { background: var(--accent); border-color: var(--accent); color: #fff; transform: rotate(0deg) scale(1.05); }
div[class*="st-key-tile_"] button p { text-align: left; margin: 0; transition: color 0.2s ease; }
div[class*="st-key-tile_"] button p:nth-child(1) { font-size: 1.9rem; line-height: 1; margin-bottom: 0.7rem; }
div[class*="st-key-tile_"] button p:nth-child(2) {
  font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.15rem; font-weight: 700; color: var(--ink);
  letter-spacing: -0.01em; text-transform: uppercase;
}
div[class*="st-key-tile_"] button p:nth-child(3) {
  font-size: 0.86rem; font-weight: 400; color: var(--muted); line-height: 1.45; margin-top: 0.35rem;
}
/* Persistent, always-visible CTA line so it is obviously interactive. */
div[class*="st-key-tile_"] button p:nth-child(4) {
  margin-top: auto; padding-top: 0.9rem; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent);
}
div[class*="st-key-tile_"] button:hover p:nth-child(2) { color: var(--paper); }
div[class*="st-key-tile_"] button:hover p:nth-child(3) { color: color-mix(in srgb, var(--paper) 70%, transparent); }
div[class*="st-key-tile_"] button:hover p:nth-child(4) { color: var(--accent-deep); }

/* ---------- Scroll reveal ---------- */
.aven-reveal {
  opacity: 0; transform: translateY(22px);
  transition: opacity 0.6s ease, transform 0.6s cubic-bezier(0.2, 0.7, 0.3, 1);
  will-change: opacity, transform;
}
.aven-reveal.aven-visible { opacity: 1; transform: translateY(0); }
.aven-reveal.stagger-0.aven-visible { transition-delay: 0.02s; }
.aven-reveal.stagger-1.aven-visible { transition-delay: 0.1s; }
.aven-reveal.stagger-2.aven-visible { transition-delay: 0.18s; }

@media (prefers-reduced-motion: reduce) {
  .aven-logo-pulse path, .aven-chevron, .aven-marquee-track, .aven-ecg-blip { animation: none; }
  .aven-reveal { opacity: 1; transform: none; transition: none; }
  div[class*="st-key-tile_"] button:hover { transform: none !important; }
}

/* ---------- Stepper (flow) ---------- */
.aven-stepper { display: flex; gap: 0.5rem; margin: 1.6rem 0 1.4rem 0; }
.aven-step {
  flex: 1; text-align: center; padding: 0.6rem 0.4rem; border-radius: 999px;
  font-size: 0.78rem; font-weight: 600; color: var(--faint);
  background: var(--card); border: 1px solid var(--line); letter-spacing: 0.02em; transition: all 0.2s ease;
}
.aven-step.active { color: var(--paper); background: var(--ink); border-color: var(--ink); }
.aven-step.done { color: var(--accent); border-color: var(--line-strong); }

.aven-boundary {
  background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 0.8rem 1rem; color: var(--muted); font-size: 0.86rem; margin: 1.4rem 0;
  display: flex; align-items: center; gap: 0.55rem;
}

/* ---------- Task switcher + branded form header ---------- */
.aven-switcher-label {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--muted); margin: 0.4rem 0 0.6rem 0;
}
div[class*="st-key-taskchip_"] button {
  border-radius: 999px !important; padding: 0.4rem 0.7rem !important; min-height: 40px;
  font-size: 0.8rem !important; font-weight: 600 !important;
  border: 1px solid var(--line-strong) !important; background: var(--card) !important;
  color: var(--muted) !important; transition: all 0.15s ease !important;
}
div[class*="st-key-taskchip_"] button:hover { border-color: var(--ink) !important; color: var(--ink) !important; transform: none !important; }
div[class*="st-key-taskchip_"] button[kind="primary"] {
  background: var(--ink) !important; color: var(--paper) !important; border-color: var(--ink) !important;
}

.aven-form-head {
  display: flex; align-items: center; gap: 1.1rem; margin: 1.6rem 0 0.8rem 0;
  padding: 1.4rem 0; border-top: 1px solid var(--line-strong); border-bottom: 1px solid var(--line);
}
.aven-form-icon {
  flex-shrink: 0; width: 54px; height: 54px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; font-size: 1.8rem;
  background: var(--accent-soft); border: 1px solid var(--line);
}
.aven-form-title { margin: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); text-transform: uppercase; }
.aven-form-blurb { margin: 0.2rem 0 0 0; color: var(--muted); font-size: 0.94rem; }

/* ---------- Result cards ---------- */
.aven-card {
  background: var(--card); border: 1px solid var(--line); border-radius: 0;
  border-left: 2px solid var(--line-strong);
  padding: 1.5rem 1.6rem; margin-bottom: 1rem; position: relative;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.aven-card:hover { transform: translateX(3px); }
.aven-card.rank-0 { border-left-color: var(--accent); }
.aven-card.rank-1 { border-left-color: var(--line-strong); }
.aven-card.rank-2 { border-left-color: var(--line-strong); }

.aven-pulse-dot {
  display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: currentColor;
  margin-right: 0.15rem; animation: aven-pulse 1.9s ease-in-out infinite;
}
@keyframes aven-pulse { 0%,100% { opacity: 0.4; transform: scale(0.85); } 50% { opacity: 1; transform: scale(1.15); } }
@media (prefers-reduced-motion: reduce) { .aven-pulse-dot { animation: none; opacity: 0.9; } }

.aven-badge {
  display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.7rem;
  border-radius: 999px; font-size: 0.76rem; font-weight: 600; white-space: nowrap;
}
.aven-badge.documented { background: var(--documented-bg); color: var(--documented-ink); }
.aven-badge.conflicting { background: var(--conflict-bg); color: var(--conflict-ink); }
.aven-badge.not_documented { background: var(--unknown-bg); color: var(--unknown-ink); }
.aven-badge.external_corroborated { background: var(--external-bg); color: var(--external-ink); }
.aven-badge.user_context { background: var(--user-bg); color: var(--user-ink); border: 1px dashed var(--user-ink); }

.aven-option-label {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--accent); margin-bottom: 0.2rem;
}
.aven-facility-name { font-size: 1.4rem; font-weight: 700; color: var(--ink); margin: 0 0 0.35rem 0; letter-spacing: -0.01em; }
.aven-fact { color: var(--muted); font-size: 0.92rem; margin: 0.2rem 0; }
.aven-fact strong { color: var(--ink); font-weight: 600; }

.aven-emergency {
  background: var(--emergency-bg); border: 1px solid var(--emergency-border);
  border-left: 4px solid var(--emergency-border);
  color: var(--emergency-ink); border-radius: 4px; padding: 1.2rem 1.3rem; margin-bottom: 1rem;
}
.aven-emergency h3 { margin-top: 0; color: var(--emergency-ink); }

/* ---------- Streamlit form widgets ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"] {
  background: var(--card) !important; border: 1px solid var(--line-strong) !important;
  border-radius: 4px !important; transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: transparent !important; color: var(--ink) !important; font-size: 0.95rem !important; padding: 0.4rem 0.5rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--faint) !important; }
.stSelectbox div[data-baseweb="select"] > div {
  background: var(--card) !important; border: 1px solid var(--line-strong) !important;
  border-radius: 4px !important; min-height: 44px; transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stSelectbox div[data-baseweb="select"] > div:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }
[data-testid="stWidgetLabel"] p, .stTextInput label p, .stTextArea label p, .stSelectbox label p, .stRadio label p {
  font-size: 0.82rem !important; font-weight: 600 !important; color: var(--ink) !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] { border-color: var(--accent) !important; }
.stRadio [role="radiogroup"] { gap: 0.4rem; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stForm"] {
  background: transparent; border: 1px solid var(--line) !important; border-radius: 6px; padding: 1.6rem 1.6rem 1.2rem 1.6rem;
}

/* ---------- Buttons: minimal editorial pills ---------- */
.stButton > button, .stRadio, .stSelectbox, .stTextInput input, .stTextArea textarea { min-height: 44px; }
.stButton > button {
  border-radius: 999px !important; font-weight: 700 !important; letter-spacing: 0.02em;
  border: 1px solid var(--line-strong) !important; color: var(--ink) !important; background: transparent !important;
  transition: all 0.16s ease !important;
}
.stButton > button:hover { border-color: var(--ink) !important; background: var(--ink) !important; color: var(--paper) !important; transform: translateY(-1px); }
.stButton > button[kind="primary"] {
  background: var(--accent) !important; color: #fff !important; border-color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover { background: var(--accent-deep) !important; border-color: var(--accent-deep) !important; }
:focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 2px; }

/* ---------- Profiles ---------- */
.aven-rating-badge {
  font-size: 0.8rem; font-weight: 700; color: var(--accent); vertical-align: middle;
  margin-left: 0.4rem; letter-spacing: 0.02em;
}
.aven-blocked-note {
  background: var(--conflict-bg); color: var(--conflict-ink); border: 1px solid var(--conflict-ink);
  border-radius: 10px; padding: 0.7rem 0.95rem; font-size: 0.86rem; font-weight: 600; margin-bottom: 1rem;
}
.aven-datasource-note {
  background: var(--unknown-bg); color: var(--muted); border: 1px solid var(--line);
  border-radius: 10px; padding: 0.7rem 0.95rem; font-size: 0.82rem; margin: 0.4rem 0 1rem 0;
}
.aven-profile-head { margin: 0.4rem 0 1.4rem 0; }
.aven-profile-card {
  background: var(--card); border: 1px solid var(--line); border-left: 2px solid var(--accent);
  border-radius: 12px; padding: 1.1rem 1.2rem; margin-bottom: 0.8rem;
}
.aven-history-row {
  display: flex; gap: 1rem; align-items: baseline; padding: 0.7rem 0;
  border-bottom: 1px solid var(--line); font-size: 0.92rem;
}
.aven-history-when {
  flex-shrink: 0; width: 8.5rem; color: var(--faint); font-size: 0.78rem;
  font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
}
.aven-history-row .dim { color: var(--faint); }
[data-testid="stMetric"] {
  background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 0.8rem 1rem;
}
[data-testid="stMetricValue"] { font-family: 'Bricolage Grotesque', sans-serif; }

.aven-footer {
  margin-top: 3rem; padding-top: 1.6rem; border-top: 1px solid var(--line);
  display: flex; flex-direction: column; gap: 0.5rem; align-items: center; text-align: center;
}
.aven-footer-boundary {
  color: var(--muted); font-size: 0.86rem; margin: 0; max-width: 60ch;
  display: inline-flex; align-items: center; gap: 0.45rem;
}

@media (max-width: 720px) {
  .aven-about-points { grid-template-columns: 1fr; }
  .aven-about-point, .aven-about-point:not(:last-child), .aven-about-point:not(:first-child) {
    border-right: none; padding-left: 0; padding-right: 0;
  }
}
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


_LIVE_STATUSES = {"documented", "external_corroborated"}


def evidence_badge_html(status: str) -> str:
    icon_key, copy = EVIDENCE_BADGES.get(status, EVIDENCE_BADGES["not_documented"])
    icon = _ICONS[icon_key]
    dot = '<span class="aven-pulse-dot"></span>' if status in _LIVE_STATUSES else ""
    return f'<span class="aven-badge {status}">{dot}{icon} {copy}</span>'


OPTION_ICONS: dict[str, str] = {
    "Best documented fit": "🥇",
    "Lower-burden route": "🧭",
    "Alternative to verify": "🔍",
}


def option_icon(label: str) -> str:
    return OPTION_ICONS.get(label, "📍")


def card_classes(index: int) -> str:
    rank = min(index, 2)
    return f"aven-card aven-reveal rank-{rank} stagger-{rank}"


# A compact heartbeat glyph used as Aven's wordmark accent; beats on a lub-dub
# rhythm via the .aven-logo-pulse animation. This is the surviving medical cue.
LOGO_PULSE_SVG = """
<svg class="aven-logo-pulse" width="44" height="28" viewBox="0 0 60 30" aria-hidden="true">
  <path d="M2,17 H16 L20,6 L26,28 L30,17 H42 L46,10 L50,24 L54,17 H58" />
</svg>
"""

# A thin ECG hairline used as a subtle section divider under the hero title.
ECG_DIVIDER_SVG = """
<svg class="aven-ecg-divider" viewBox="0 0 340 22" preserveAspectRatio="none" aria-hidden="true">
  <path d="M0,11 H150 l6,0 l5,-6 l5,12 l6,-17 l6,22 l5,-11 l6,0 H340" />
  <circle class="aven-ecg-blip" cx="178" cy="11" r="2.4" fill="currentColor" style="fill:var(--accent)" />
</svg>
"""


def marquee_html(phrases: list[str]) -> str:
    """Build a seamless scrolling marquee. The phrase list is rendered twice so
    a -50% translate loops without a visible seam."""
    items = "".join(f"<span>{p}</span>" for p in phrases)
    return (
        '<div class="aven-marquee" aria-hidden="true">'
        f'<div class="aven-marquee-track">{items}{items}</div>'
        "</div>"
    )


# Runs inside the components.html iframe, which shares the parent document's
# origin, so it can reach into the real page and observe elements there.
# Elements already on screen at load reveal immediately; anything below the
# fold reveals as the user scrolls to it. The timeout is a safety net: if the
# observer never attaches for any reason, content still becomes visible
# rather than staying hidden forever.
SCROLL_REVEAL_JS = """
<script>
(function () {
  try {
    var doc = window.parent.document;
    var reveal = function (el) { el.classList.add("aven-visible"); };
    var targets = doc.querySelectorAll(".aven-reveal:not(.aven-observed)");
    if (!targets.length) { return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          reveal(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });
    targets.forEach(function (el) {
      el.classList.add("aven-observed");
      io.observe(el);
    });
    window.setTimeout(function () {
      doc.querySelectorAll(".aven-reveal:not(.aven-visible)").forEach(reveal);
    }, 4000);
  } catch (err) {
    // Cross-origin or blocked script access: fail safe, do nothing further.
  }
})();
</script>
"""
