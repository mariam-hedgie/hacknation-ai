import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import { FEATURE_TILES_EN, STEP_KEYS, STRINGS, TASK_QUESTIONS, scaleLabel, tileCopy, tx } from "../i18n/copy";
import { useGovernedCopy } from "../i18n/governed";
import { api, type ServiceStatus } from "../api";
import { Stepper } from "../components/Stepper";

type Urgency = "Routine" | "Soon" | "Urgent";
const TRAVEL_MODES = ["walk", "bicycle", "motorbike", "bus", "train", "car", "taxi", "plane", "ambulance"];

function defaultArrivalDate() {
  const date = new Date();
  date.setDate(date.getDate() + 3);
  return date.toISOString().slice(0, 10);
}

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
  const [maxDistance, setMaxDistance] = useState("100");
  const [travelModes, setTravelModes] = useState<string[]>(["bus", "train"]);
  const [travelBudget, setTravelBudget] = useState("");
  const [careBudget, setCareBudget] = useState("");
  const [arrivalDate, setArrivalDate] = useState(defaultArrivalDate);
  const [preference, setPreference] = useState<"Either" | "Public" | "Private">("Either");
  const [prefLanguage, setPrefLanguage] = useState("");
  const [emergencyChecked, setEmergencyChecked] = useState(false);
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [allowOpenAI, setAllowOpenAI] = useState(false);
  const [structuring, setStructuring] = useState(false);
  const [structureMessage, setStructureMessage] = useState("");
  const [voiceConsent, setVoiceConsent] = useState(false);
  const [recording, setRecording] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    const presetState = location.state as { careTask?: string; emergency?: boolean } | null;
    const preset = presetState?.careTask;
    if (preset) setCareTask(preset);
    setEmergencyChecked(Boolean(presetState?.emergency));
    setEmergencyReported(Boolean(presetState?.emergency));
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    api.serviceStatus().then(setStatus).catch(() => {});
  }, []);

  const meta = tileCopy(language, careTask);

  const toggleTravelMode = (mode: string) => {
    setTravelModes((current) =>
      current.includes(mode) ? current.filter((item) => item !== mode) : [...current, mode],
    );
  };

  const structureWithOpenAI = async () => {
    setStructureMessage("");
    if (!message.trim()) {
      setStructureMessage("Describe what you need in the notes box first.");
      return;
    }
    setStructuring(true);
    try {
      const draft = await api.structureIntake(message);
      setCareTask(draft.care_task);
      if (draft.capability) setDetail(draft.capability);
      if (draft.location) setLocationInput(draft.location);
      setUrgency((draft.urgency[0].toUpperCase() + draft.urgency.slice(1)) as Urgency);
      if (draft.travel_modes.length) setTravelModes(draft.travel_modes);
      if (draft.language) setPrefLanguage(draft.language);
      setStructureMessage(draft.clarification_question || "Draft filled. Review every field before continuing.");
    } catch {
      setStructureMessage("OpenAI structuring is not configured right now. Continue with the form.");
    } finally {
      setStructuring(false);
    }
  };

  const startRecording = async () => {
    setVoiceMessage("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const reader = new FileReader();
        reader.onloadend = async () => {
          const encoded = String(reader.result).split(",")[1] || "";
          try {
            const transcript = await api.transcribe(encoded, language);
            setMessage(transcript.text);
            setVoiceMessage("Transcript added to your notes. Read and correct it before continuing.");
          } catch {
            setVoiceMessage("Transcription failed. Use typed input.");
          }
        };
        reader.readAsDataURL(blob);
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setVoiceMessage("Microphone access was not available. Use typed input.");
    }
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
    setRecording(false);
  };

  const submit = () => {
    setDraftRequest({
      message: message || null,
      care_task: careTask,
      capability: detail || message || "the care need you described",
      location: locationInput || "not provided",
      urgency: urgency.toLowerCase(),
      travel_tolerance: Number(maxDistance) <= 25 ? "low" : Number(maxDistance) <= 150 ? "medium" : "high",
      budget_sensitivity: careBudget ? "high" : "medium",
      facility_preference: preference.toLowerCase(),
      language: prefLanguage || null,
      medication_name: careTask === "refill" ? detail : null,
      has_current_prescription: careTask === "refill" ? hasPrescription : null,
      has_clinician_order: careTask === "lab" ? { yes: true, no: false, unsure: null }[labOrder] : null,
      emergency_warning_reported: emergencyReported,
      max_distance_km: Number(maxDistance) || null,
      travel_modes: travelModes,
      travel_budget_rupees: travelBudget ? Number(travelBudget) : null,
      care_budget_rupees: careBudget ? Number(careBudget) : null,
      required_arrival_date: arrivalDate || null,
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
          {status && !status.voice_available && <p className="fact">Voice input: {status.voice_message}</p>}

          <div className="form-card reveal visible">
            <div className="section-title" style={{ marginBottom: "1rem" }}>
              {tx(language, "specifics")}
            </div>

            {status?.voice_available && (
              <details className="disclosure">
                <summary>Optional voice input</summary>
                <label className="checkbox-row">
                  <input type="checkbox" checked={voiceConsent} onChange={(e) => setVoiceConsent(e.target.checked)} />
                  <span>I agree to send this recording to ElevenLabs for transcription.</span>
                </label>
                <button className="btn" disabled={!voiceConsent} onClick={recording ? stopRecording : startRecording}>
                  {recording ? "Stop recording" : "Transcribe for review"}
                </button>
                {voiceMessage && <div className="alert alert-info">{voiceMessage}</div>}
              </details>
            )}

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

            <details className="disclosure">
              <summary>Optional: Structure with OpenAI</summary>
              <p className="hint">
                This only turns your own notes into an editable draft. It does not diagnose, search, or choose a hospital.
              </p>
              <label className="checkbox-row">
                <input type="checkbox" checked={allowOpenAI} onChange={(e) => setAllowOpenAI(e.target.checked)} />
                <span>I agree to send only this note to OpenAI and review the result.</span>
              </label>
              <button className="btn" disabled={!allowOpenAI || structuring} onClick={structureWithOpenAI}>
                {structuring ? "Structuring…" : "Fill an editable draft"}
              </button>
              {structureMessage && <div className="alert alert-info">{structureMessage}</div>}
            </details>

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
              <div className="field">
                <label>Required arrival date</label>
                <input type="date" value={arrivalDate} onChange={(e) => setArrivalDate(e.target.value)} />
              </div>
            </div>
            <div className="field-row">
              <div className="field">
                <label>Maximum travel distance (km)</label>
                <input type="number" min="1" max="5000" value={maxDistance} onChange={(e) => setMaxDistance(e.target.value)} />
              </div>
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
              <label>Travel modes</label>
              <div className="radio-row">
                {TRAVEL_MODES.map((mode) => (
                  <button key={mode} type="button" className={`radio-pill ${travelModes.includes(mode) ? "selected" : ""}`} onClick={() => toggleTravelMode(mode)}>
                    {mode}
                  </button>
                ))}
              </div>
              <p className="hint">Select every mode you could realistically use. Ambulance service is always verified separately.</p>
            </div>
            <div className="field-row">
              <div className="field">
                <label>Travel budget (₹, optional)</label>
                <input type="number" min="0" value={travelBudget} onChange={(e) => setTravelBudget(e.target.value)} />
              </div>
              <div className="field">
                <label>Care budget (₹, optional)</label>
                <input type="number" min="0" value={careBudget} onChange={(e) => setCareBudget(e.target.value)} />
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
