import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppState, blockFacility, isBlocked } from "../state/AppState";
import { STEP_KEYS, STRINGS, FEEDBACK_OPTIONS } from "../i18n/copy";
import { api, type PlanOption, type ServiceStatus, type TravelCapability } from "../api";
import { Stepper } from "../components/Stepper";
import { OptionCard } from "../components/OptionCard";
import { OptionIcon, IconMapPin, IconDatabase, IconBan } from "../components/Icons";

const EVIDENCE_DEFAULTS: Record<string, string> = {
  "Best documented fit": "documented",
  "Lower-burden route": "not_documented",
  "Alternative to verify": "conflicting",
};

const TRAVEL_MODES = ["walk", "bus", "train", "car", "taxi"];

export function Results() {
  const navigate = useNavigate();
  const { language, draftRequest, planResponse, profile, persistProfile, saveOption, savedPlans, feedback, setFeedback, persistenceMode, persistenceError } =
    useAppState();
  const strings = STRINGS[language];
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [travelCaps, setTravelCaps] = useState<TravelCapability[] | null>(null);
  const [feedbackLabel, setFeedbackLabel] = useState(Object.keys(FEEDBACK_OPTIONS)[0]);
  const [feedbackNote, setFeedbackNote] = useState("");
  const [savedMsg, setSavedMsg] = useState(false);

  useEffect(() => {
    if (!planResponse || planResponse.safety_branch !== "proceed") {
      navigate("/intake");
    }
  }, [planResponse, navigate]);

  useEffect(() => {
    api.serviceStatus().then(setStatus).catch(() => {});
  }, []);

  if (!planResponse || planResponse.safety_branch !== "proceed" || !draftRequest) return null;

  const options: PlanOption[] = planResponse.options.map((opt) => ({
    ...opt,
    evidence_status: opt.evidence_status ?? EVIDENCE_DEFAULTS[opt.label] ?? "not_documented",
  }));
  const visible = options.filter((o) => !isBlocked(profile, o.facility));
  const hiddenCount = options.length - visible.length;

  const loadTravelTruth = () => {
    if (travelCaps) return;
    api.travelCapabilities(TRAVEL_MODES).then(setTravelCaps).catch(() => {});
  };

  return (
    <div className="page flow-page">
      <Stepper current={STEP_KEYS.indexOf("results")} labels={strings.steps} />

      <div className="results-layout">
        <div className="options-col">
          <div className="section-title" style={{ marginBottom: "0.4rem" }}>
            Best next step
          </div>
          <p className="hint">
            For: {draftRequest.capability} · Starting from: {draftRequest.location}
          </p>

          {status && status.backend_mode !== "live" && (
            status.tools.local_data ? (
              <div className="datasource-note">
                📍 Real facility data from a local snapshot — not a live Databricks connection. Evidence below is
                source-grounded, but confirm anything time-sensitive (availability, hours, price) by phone.
              </div>
            ) : (
              <div className="datasource-note">
                ⚙️ Seeded demo data — the Databricks evidence pipeline (Vector Search · Agent Bricks · Lakebase) is not
                connected in this environment. Every option is labelled as a demo.
              </div>
            )
          )}

          <details className="disclosure">
            <summary>What is connected right now</summary>
            {status && (
              <div>
                <p className="fact">
                  <strong>Evidence pipeline:</strong>{" "}
                  {status.backend_mode === "live"
                    ? "Live Databricks evidence"
                    : status.tools.local_data
                      ? "Real facility data (local snapshot) — not a live Databricks connection"
                      : "Seeded demo data — Vector Search and Agent Bricks are not connected"}
                </p>
                <p className="fact">
                  <strong>Routing provider:</strong> {status.map_provider}
                  {status.map_live_provider ? " (live)" : " (offline estimates only)"}
                </p>
                <p className="fact">
                  <strong>Facility database:</strong> Databricks SQL {status.databricks_mode}
                </p>
                <p className="fact">
                  <strong>Voice input:</strong> {status.voice_message}
                </p>
              </div>
            )}
          </details>

          {hiddenCount > 0 && (
            <div className="blocked-note">
              🚫 {hiddenCount} option(s) hidden because you asked not to be referred there. Manage this in your
              profile.
            </div>
          )}

          {visible.length === 0 && (
            <div className="alert alert-info">
              Every documented option here is on your blocklist. Unblock a facility in your profile to see routes
              again.
            </div>
          )}

          {visible.map((option, index) => (
            <OptionCard
              key={option.facility + index}
              index={index}
              option={option}
              request={draftRequest}
              rating={null}
              isBlocked={false}
              onSave={async (note) => {
                const saved = await saveOption(option, draftRequest.care_task, note);
                setSavedMsg(saved);
                return saved;
              }}
              onBlock={() => persistProfile(blockFacility(profile, option.facility))}
            />
          ))}

          {visible.length > 0 && (
            <details className="disclosure" onToggle={loadTravelTruth}>
              <summary>What we can and cannot tell you about travel</summary>
              <p className="hint">
                Travel figures above are estimates for comparison. None of them is a live route, a fare quote, or
                confirmation that a service is running.
              </p>
              {travelCaps?.map((row) => (
                <p className="fact" key={row.mode}>
                  <strong>{row.mode[0].toUpperCase() + row.mode.slice(1)}:</strong> {row.label}
                </p>
              ))}
            </details>
          )}

          {savedMsg && <div className="alert alert-success">Saved — reopen it from My plans. {persistenceMode === "lakebase" ? "Lakebase confirmed the write." : "This is local-demo storage only."}</div>}
          {persistenceError && <div className="alert alert-warning">{persistenceError}</div>}

          <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>
            Was this plan useful?
          </div>
          <div className="field">
            <label>What happened?</label>
            <select value={feedbackLabel} onChange={(e) => setFeedbackLabel(e.target.value)}>
              {Object.keys(FEEDBACK_OPTIONS).map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Optional correction or note</label>
            <input type="text" value={feedbackNote} onChange={(e) => setFeedbackNote(e.target.value)} />
          </div>
          <button
            className="btn"
            onClick={() => void setFeedback(FEEDBACK_OPTIONS[feedbackLabel], feedbackNote)}
          >
            Save feedback
          </button>
          {feedback && (
            <div className="alert alert-success">Feedback saved for this demo session. It does not change facility evidence.</div>
          )}

          <div className="btn-row">
            <button className="btn btn-primary" onClick={() => navigate("/intake")}>
              Start a new request
            </button>
          </div>
        </div>

        <div className="side-col">
          {savedPlans.length > 0 && (
            <div className="card">
              <div className="section-title" style={{ marginBottom: "0.6rem" }}>
                My plans
              </div>
              {savedPlans.map((plan, i) => (
                <p className="fact" key={i}>
                  {OPTION_ICONS[plan.label] ?? "📍"} <strong>{plan.facility}</strong> — {plan.label}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
