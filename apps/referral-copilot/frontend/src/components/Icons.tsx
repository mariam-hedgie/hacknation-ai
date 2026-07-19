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
