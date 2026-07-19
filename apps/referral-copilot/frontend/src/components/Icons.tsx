import type { ReactNode } from "react";

export function LogoPulse() {
  return (
    <svg className="logo-pulse" width="34" height="22" viewBox="0 0 60 30" aria-hidden="true">
      <path d="M2,17 H16 L20,6 L26,28 L30,17 H42 L46,10 L50,24 L54,17 H58" />
    </svg>
  );
}

export function EcgDivider() {
  return (
    <svg className="ecg-divider" width="min(340px, 60%)" height="22" viewBox="0 0 340 22" preserveAspectRatio="none" aria-hidden="true" style={{ width: "min(340px, 60%)", display: "block", margin: "0.4rem auto 0" }}>
      <path d="M0,11 H150 l6,0 l5,-6 l5,12 l6,-17 l6,22 l5,-11 l6,0 H340" />
      <circle className="ecg-blip" cx="178" cy="11" r="2.4" style={{ fill: "var(--accent)" }} />
    </svg>
  );
}

/* ---------- Shared line-icon primitives ---------- */

interface IconProps {
  size?: number;
  className?: string;
}

function Glyph({ size = 20, className, children }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

/* Care-task icons */

function IconClipboardPulse(p: IconProps) {
  return (
    <Glyph {...p}>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <rect x="9" y="2" width="6" height="4" rx="1" />
      <path d="M8 13h1.6l1-2 1.6 4 1-2H16" />
    </Glyph>
  );
}

function IconCapsule(p: IconProps) {
  return (
    <Glyph {...p}>
      <rect x="2.5" y="8.5" width="19" height="7" rx="3.5" />
      <path d="M12 8.5v7" />
    </Glyph>
  );
}

function IconTestTube(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M9 3h6" />
      <path d="M10 3v13a2 2 0 0 0 4 0V3" />
      <path d="M10 10h4" />
    </Glyph>
  );
}

function IconDroplet(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z" />
    </Glyph>
  );
}

function IconCalendar(p: IconProps) {
  return (
    <Glyph {...p}>
      <rect x="3.5" y="5" width="17" height="16" rx="2" />
      <path d="M3.5 9.5h17" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </Glyph>
  );
}

function IconCompass(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M16 8l-2.4 5.6L8 16l2.4-5.6L16 8Z" />
    </Glyph>
  );
}

/* Option-rank icons */

function IconAward(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="12" cy="8.5" r="5.5" />
      <path d="M8.5 12.6 7 21l5-2.8L17 21l-1.5-8.4" />
    </Glyph>
  );
}

function IconNavigation(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M12 2.5 19.5 21 12 16.8 4.5 21 12 2.5Z" />
    </Glyph>
  );
}

function IconSearch(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="11" cy="11" r="7" />
      <path d="M20.5 20.5 16.5 16.5" />
    </Glyph>
  );
}

/* Evidence-status icons */

function IconCheckCircle(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 12.2l2.4 2.4 4.6-5" />
    </Glyph>
  );
}

function IconAlertTriangle(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M12 3.5 22 20H2L12 3.5Z" />
      <path d="M12 9.5v5" />
      <path d="M12 17.5h.01" />
    </Glyph>
  );
}

function IconHelpCircle(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.6 9.4a2.5 2.5 0 0 1 4.6 1.2c0 1.7-2.2 2.2-2.2 3.4" />
      <path d="M12 17.5h.01" />
    </Glyph>
  );
}

function IconLink(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1" />
      <path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1" />
    </Glyph>
  );
}

function IconNote(p: IconProps) {
  return (
    <Glyph {...p}>
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M9 8h6" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </Glyph>
  );
}

/* Standalone glyphs */

export function IconShield(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M12 3l7 3v5c0 4.6-3.2 7.8-7 9-3.8-1.2-7-4.4-7-9V6l7-3Z" />
    </Glyph>
  );
}

export function IconBan(p: IconProps) {
  return (
    <Glyph {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M5.6 5.6 18.4 18.4" />
    </Glyph>
  );
}

export function IconMapPin(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M12 21s7-5.6 7-11a7 7 0 0 0-14 0c0 5.4 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </Glyph>
  );
}

export function IconDatabase(p: IconProps) {
  return (
    <Glyph {...p}>
      <ellipse cx="12" cy="5" rx="7.5" ry="3" />
      <path d="M4.5 5v14c0 1.6 3.4 3 7.5 3s7.5-1.4 7.5-3V5" />
      <path d="M4.5 12c0 1.6 3.4 3 7.5 3s7.5-1.4 7.5-3" />
    </Glyph>
  );
}

export function IconChevronDown(p: IconProps) {
  return (
    <Glyph {...p}>
      <path d="M6 9l6 6 6-6" />
    </Glyph>
  );
}

/* ---------- Keyed registries ---------- */

type IconComponent = (props: IconProps) => ReactNode;

const TASK_ICONS: Record<string, IconComponent> = {
  known_referral: IconClipboardPulse,
  refill: IconCapsule,
  lab: IconTestTube,
  vaccination: IconDroplet,
  follow_up: IconCalendar,
  symptom_first: IconCompass,
};

export function TaskIcon({ name, ...props }: IconProps & { name: string }) {
  const Component = TASK_ICONS[name] ?? IconCompass;
  return <Component {...props} />;
}

const OPTION_ICON_MAP: Record<string, IconComponent> = {
  "Best documented fit": IconAward,
  "Lower-burden route": IconNavigation,
  "Alternative to verify": IconSearch,
};

export function OptionIcon({ label, ...props }: IconProps & { label: string }) {
  const Component = OPTION_ICON_MAP[label] ?? IconMapPin;
  return <Component {...props} />;
}

const EVIDENCE_ICON_MAP: Record<string, IconComponent> = {
  documented: IconCheckCircle,
  conflicting: IconAlertTriangle,
  not_documented: IconHelpCircle,
  external_corroborated: IconLink,
  user_context: IconNote,
};

export function EvidenceIcon({ status, ...props }: IconProps & { status: string }) {
  const Component = EVIDENCE_ICON_MAP[status] ?? IconHelpCircle;
  return <Component {...props} />;
}
