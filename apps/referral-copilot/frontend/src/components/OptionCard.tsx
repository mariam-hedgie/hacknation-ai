import { useState } from "react";
import type { PlanOption, PlanRequestBody } from "../api";
import { EvidenceBadge } from "./Evidence";
import { EnrichmentView } from "./EnrichmentView";
import { EVIDENCE_STATUS_KEYS, useGovernedCopy } from "../i18n/governed";
import { OPTION_ICONS } from "../i18n/copy";
import { Reveal } from "./Reveal";
import { JourneyPanel } from "./JourneyPanel";

interface Props {
  index: number;
  option: PlanOption;
  request: PlanRequestBody;
  rating: number | null;
  isBlocked: boolean;
  onSave: (note: string) => Promise<boolean>;
  onBlock: () => void;
}

export function OptionCard({ index, option, request, rating, isBlocked, onSave, onBlock }: Props) {
  const { get } = useGovernedCopy();
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [note, setNote] = useState("");
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
        <JourneyPanel option={option} request={request} />

        <details className="disclosure">
          <summary>Add a note before saving (optional)</summary>
          <div className="field">
            <label>Private planning note</label>
            <textarea maxLength={500} value={note} onChange={(event) => setNote(event.target.value)} placeholder="For example: verify wheelchair entrance before travel" />
            <p className="hint">Only this decision and note are retained. Your health intake, location, medication, voice, and transcript are not saved.</p>
          </div>
        </details>

        <div className="button-cols">
          <button
            className="btn"
            disabled={saveStatus === "saving" || saveStatus === "saved"}
            onClick={async () => {
              setSaveStatus("saving");
              setSaveStatus(await onSave(note) ? "saved" : "error");
            }}
          >
            {saveStatus === "saving" ? "Saving…" : saveStatus === "saved" ? "Saved" : "Save plan"}
          </button>
          {saveStatus === "error" && <span className="save-error">Not saved. Secure storage did not confirm the write.</span>}
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
