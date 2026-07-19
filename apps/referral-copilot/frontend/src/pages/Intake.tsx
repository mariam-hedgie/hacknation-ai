import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import { FEATURE_TILES_EN, STEP_KEYS, STRINGS, TASK_QUESTIONS, scaleLabel, tileCopy, tx } from "../i18n/copy";
import { useGovernedCopy } from "../i18n/governed";
import { api, type ServiceStatus } from "../api";
import { Stepper } from "../components/Stepper";

type Urgency = "Routine" | "Soon" | "Urgent";
type Level = "Low" | "Medium" | "High";

export function Intake() {
  const navigate = useNavigate();
  const location = useLocation();
  const { language, careTask, setCareTask, emergencyReported, setEmergencyReported, setDraftRequest } = useAppState();
  const { get } = useGovernedCopy();
  const strings = STRINGS[language];

  const [detail, setDetail] = useState("");
  const [locationInput, setLocationInput] = useState("");
  const [hasPrescription, setHasPrescription] = useState(false);
  const [labOrder, setLabOrder] = useState<"yes" | "unsure" | "no">("unsure");
  const [message, setMessage] = useState("");
  const [urgency, setUrgency] = useState<Urgency>("Soon");
  const [travel, setTravel] = useState<Level>("Medium");
  const [budget, setBudget] = useState<Level>("High");
  const [preference, setPreference] = useState<"Either" | "Public" | "Private">("Either");
  const [prefLanguage, setPrefLanguage] = useState("");
  const [emergencyChecked, setEmergencyChecked] = useState(false);
  const [status, setStatus] = useState<ServiceStatus | null>(null);

  useEffect(() => {
    const preset = (location.state as { careTask?: string } | null)?.careTask;
    if (preset) setCareTask(preset);
    // Reset the emergency checkbox on every fresh entry into intake.
    setEmergencyChecked(false);
    setEmergencyReported(false);
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    api.serviceStatus().then(setStatus).catch(() => {});
  }, []);

  const meta = tileCopy(language, careTask);

  const submit = () => {
    setDraftRequest({
      message: message || null,
      care_task: careTask,
      capability: detail || message || "the care need you described",
      location: locationInput || "not provided",
      urgency: urgency.toLowerCase(),
      travel_tolerance: travel.toLowerCase(),
      budget_sensitivity: budget.toLowerCase(),
      facility_preference: preference.toLowerCase(),
      language: prefLanguage || null,
      medication_name: careTask === "refill" ? detail : null,
      has_current_prescription: careTask === "refill" ? hasPrescription : null,
      has_clinician_order: careTask === "lab" ? { yes: true, no: false, unsure: null }[labOrder] : null,
      emergency_warning_reported: emergencyReported,
    });
    navigate("/confirm");
  };

  return (
    <div className="page flow-page">
      <Stepper current={STEP_KEYS.indexOf("intake")} labels={strings.steps} />

      <div className="switcher-label">{tx(language, "switcher_label")}</div>
      <div className="switcher-row">
        {FEATURE_TILES_EN.map((tile) => {
          const copy = tileCopy(language, tile.key);
          return (
            <button
              key={tile.key}
              className={`task-chip ${careTask === tile.key ? "active" : ""}`}
              onClick={() => setCareTask(tile.key)}
            >
              {tile.icon} {copy.title}
            </button>
          );
        })}
      </div>

      <div className="form-head">
        <div className="form-icon">{meta.icon}</div>
        <div>
          <h2 className="form-title">{meta.title}</h2>
          <p className="form-blurb">{meta.desc}</p>
        </div>
      </div>

      {careTask === "symptom_first" && (
        <>
          <div className="alert alert-warning">{get("emergency_intake_warning")}</div>
          <label className="checkbox-row" style={{ marginBottom: "1rem" }}>
            <input
              type="checkbox"
              checked={emergencyChecked}
              onChange={(e) => {
                setEmergencyChecked(e.target.checked);
                setEmergencyReported(e.target.checked);
              }}
            />
            <span>{get("emergency_intake_checkbox")}</span>
          </label>
        </>
      )}

      {careTask === "symptom_first" && emergencyChecked ? (
        <EmergencyPanel onRestart={() => setEmergencyChecked(false)} />
      ) : (
        <>
          {status && <p className="fact">🎤 {status.voice_message}</p>}

          <div className="form-card reveal visible">
            <div className="section-title" style={{ marginBottom: "1rem" }}>
              {tx(language, "specifics")}
            </div>

            <div className="field">
              <label>{meta.detail_label}</label>
              <input
                type="text"
                value={detail}
                onChange={(e) => setDetail(e.target.value)}
                placeholder={TASK_QUESTIONS[careTask]}
              />
            </div>
            <div className="field">
              <label>{tx(language, "location_label")}</label>
              <input
                type="text"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder={tx(language, "location_ph")}
              />
            </div>

            {careTask === "refill" && (
              <div className="field">
                <label className="checkbox-row">
                  <input type="checkbox" checked={hasPrescription} onChange={(e) => setHasPrescription(e.target.checked)} />
                  <span>{tx(language, "refill_rx_label")}</span>
                </label>
                <p className="hint">{tx(language, "refill_rx_help")}</p>
              </div>
            )}

            {careTask === "lab" && (
              <div className="field">
                <label>{tx(language, "lab_order_label")}</label>
                <div className="radio-row">
                  {(["yes", "unsure", "no"] as const).map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`radio-pill ${labOrder === opt ? "selected" : ""}`}
                      onClick={() => setLabOrder(opt)}
                    >
                      {tx(language, "lab_order_options")[opt]}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="field">
              <label>{tx(language, "extra_label")}</label>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={tx(language, "extra_ph")} />
            </div>

            <div className="section-title" style={{ margin: "1.4rem 0 1rem" }}>
              {tx(language, "prefs")}
            </div>
            <p className="hint" style={{ marginTop: "-0.6rem", marginBottom: "1rem" }}>
              {tx(language, "prefs_why")}
            </p>

            <div className="field-row">
              <SliderField
                label={tx(language, "urgency_label")}
                options={["Routine", "Soon", "Urgent"] as const}
                value={urgency}
                onChange={setUrgency}
                labelFor={(v) => scaleLabel(language, v)}
              />
              <SliderField
                label={tx(language, "travel_label")}
                options={["Low", "Medium", "High"] as const}
                value={travel}
                onChange={setTravel}
                labelFor={(v) => scaleLabel(language, v)}
              />
            </div>
            <div className="field-row">
              <SliderField
                label={tx(language, "budget_label")}
                options={["Low", "Medium", "High"] as const}
                value={budget}
                onChange={setBudget}
                labelFor={(v) => scaleLabel(language, v)}
              />
              <div className="field">
                <label>{tx(language, "facility_label")}</label>
                <div className="radio-row">
                  {(["Either", "Public", "Private"] as const).map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`radio-pill ${preference === opt ? "selected" : ""}`}
                      onClick={() => setPreference(opt)}
                    >
                      {scaleLabel(language, opt)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="field">
              <label>{tx(language, "language_label")}</label>
              <input type="text" value={prefLanguage} onChange={(e) => setPrefLanguage(e.target.value)} />
            </div>

            <button className="btn btn-primary btn-block" onClick={submit}>
              {tx(language, "submit")}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function SliderField<T extends string>({
  label,
  options,
  value,
  onChange,
  labelFor,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  labelFor: (v: string) => string;
}) {
  const index = options.indexOf(value);
  return (
    <div className="field">
      <label>{label}</label>
      <div className="slider-track">
        <input
          type="range"
          min={0}
          max={options.length - 1}
          step={1}
          value={index}
          onChange={(e) => onChange(options[Number(e.target.value)])}
        />
        <div className="slider-labels">
          {options.map((opt) => (
            <span key={opt} style={{ fontWeight: opt === value ? 700 : 400, color: opt === value ? "var(--ink)" : undefined }}>
              {labelFor(opt)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function EmergencyPanel({ onRestart }: { onRestart: () => void }) {
  const { get } = useGovernedCopy();
  return (
    <div className="emergency-panel">
      <h3>{get("emergency_title")}</h3>
      <p>{get("emergency_body")}</p>
      <button className="btn" onClick={onRestart}>
        {get("emergency_restart")}
      </button>
    </div>
  );
}
