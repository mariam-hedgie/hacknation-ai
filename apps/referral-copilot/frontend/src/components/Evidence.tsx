import { EvidenceIcon } from "./Icons";

const LIVE_STATUSES = new Set(["documented", "external_corroborated"]);

export function EvidenceBadge({ status, label }: { status: string; label: string }) {
  return (
    <span className={`badge ${status}`}>
      {LIVE_STATUSES.has(status) && <span className="pulse-dot" />}
      <EvidenceIcon status={status} size={14} />
      {label}
    </span>
  );
}

export function TrustChip({ label, explanation }: { label: string; explanation: string }) {
  return (
    <div className="trust-chip">
      <span className="trust-label">{label}</span>
      <span className="trust-why">{explanation}</span>
    </div>
  );
}

export function QualityNote({ text, sparse = false }: { text: string; sparse?: boolean }) {
  return <div className={`quality-note ${sparse ? "sparse" : ""}`}>{text}</div>;
}

export function Chips({ labels }: { labels: string[] }) {
  if (!labels.length) return null;
  return (
    <div className="chips">
      {labels.map((label) => (
        <span className="chip" key={label}>
          {label}
        </span>
      ))}
    </div>
  );
}
