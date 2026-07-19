import { useState } from "react";
import type { PlanOption } from "../api";
import { EvidenceBadge } from "./Evidence";
import { EnrichmentView } from "./EnrichmentView";
import { EVIDENCE_STATUS_KEYS, useGovernedCopy } from "../i18n/governed";
import { OPTION_ICONS } from "../i18n/copy";
import { Reveal } from "./Reveal";

interface Props {
  index: number;
  option: PlanOption;
  rating: number | null;
  isBlocked: boolean;
  onSave: () => void;
  onBlock: () => void;
}

export function OptionCard({ index, option, rating, isBlocked, onSave, onBlock }: Props) {
  const { get } = useGovernedCopy();
  const [saved, setSaved] = useState(false);
  const evidenceStatus = option.evidence_status ?? "not_documented";
  const icon = OPTION_ICONS[option.label] ?? "📍";
  const rank = Math.min(index, 2);

  return (
    <Reveal delayMs={rank * 80}>
      <div className={`card rank-${rank}`}>
        <div className="card-top">
          <div>
            <div className="option-label">
              {icon} {option.label}
            </div>
            <p className="facility-name">
              {option.facility}
              {rating && <span className="rating-badge">★ {rating}/5</span>}
            </p>
          </div>
          <EvidenceBadge status={evidenceStatus} label={get(EVIDENCE_STATUS_KEYS[evidenceStatus] ?? "not_confirmed")} />
        </div>

        <p className="fact">{option.summary}</p>
        <p className="fact">
          <strong>{option.travel}</strong>
        </p>
        <p className="fact">
          <strong>{option.cost}</strong>
        </p>
        <p className="fact">
          <strong>What to do next:</strong> {option.next_step}
        </p>

        <EnrichmentView enrichment={option.enrichment} />

        <div className="button-cols">
          <button
            className="btn"
            onClick={() => {
              onSave();
              setSaved(true);
            }}
          >
            {saved ? "Saved ✓" : "Save plan"}
          </button>
          <button className="btn" onClick={onBlock} disabled={isBlocked}>
            {isBlocked ? "Blocked" : "🚫 Never refer me here"}
          </button>
          <details className="disclosure" style={{ flex: 1, minWidth: 140 }}>
            <summary>Why this option?</summary>
            <div>
              <p className="fact">
                <strong>{get("what_we_could_not_confirm")}</strong>
              </p>
              <p className="fact">{option.unknowns}</p>
              <p className="fact">
                <strong>Ranking explanation</strong>
              </p>
              <p className="fact">{option.ranking}</p>
              <p className="fact">
                <strong>Evidence</strong>
              </p>
              <p className="fact">{option.evidence}</p>
            </div>
          </details>
        </div>
      </div>
    </Reveal>
  );
}
