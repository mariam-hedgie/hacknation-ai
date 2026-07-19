import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppState, addHistory } from "../state/AppState";
import { STEP_KEYS, STRINGS, tx } from "../i18n/copy";
import { useGovernedCopy, type GovernedKey } from "../i18n/governed";
import type { PlanResponse } from "../api";
import { api } from "../api";
import { Stepper } from "../components/Stepper";
import { EmergencyPanel } from "./Intake";

export function Confirm() {
  const navigate = useNavigate();
  const { language, draftRequest, planResponse, setPlanResponse, profile, persistProfile } = useAppState();
  const { get } = useGovernedCopy();
  const strings = STRINGS[language];
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!draftRequest) navigate("/intake");
  }, [draftRequest, navigate]);

  if (!draftRequest) return null;

  const summary = tx(language, "confirm_summary")
    .replace("**{capability}**", `**${draftRequest.capability}**`)
    .replace("**{location}**", `**${draftRequest.location}**`)
    .replace("**{urgency}**", `**${draftRequest.urgency}**`)
    .replace("**{travel_tolerance} travel burden**", `**${draftRequest.travel_tolerance} travel burden**`)
    .replace("**{facility_preference}**", `**${draftRequest.facility_preference}**`)
    .split("**")
    .map((chunk, i) => (i % 2 === 1 ? <strong key={i}>{chunk}</strong> : chunk));

  const confirmAndPlan = async () => {
    setLoading(true);
    try {
      const response = await api.plan(draftRequest);
      setPlanResponse(response);
      if (response.safety_branch === "proceed") {
        persistProfile(
          addHistory(profile, {
            care_task: draftRequest.care_task,
            capability: draftRequest.capability ?? "",
            location: draftRequest.location ?? "",
          }),
        );
        navigate("/results");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page flow-page flow-narrow">
      <Stepper current={STEP_KEYS.indexOf("confirm")} labels={strings.steps} />

      <div className="section-title" style={{ marginBottom: "0.8rem" }}>
        {tx(language, "confirm_title")}
      </div>
      <p style={{ maxWidth: "70ch" }}>{summary}</p>

      <details className="disclosure">
        <summary>{tx(language, "confirm_see_fields")}</summary>
        <div>
          <p className="fact"><strong>Arrive by:</strong> {draftRequest.required_arrival_date || "Not specified"}</p>
          <p className="fact"><strong>Travel modes:</strong> {draftRequest.travel_modes?.join(", ") || "Not specified"}</p>
          <p className="fact"><strong>Maximum distance:</strong> {draftRequest.max_distance_km ? `${draftRequest.max_distance_km} km` : "Not specified"}</p>
          <p className="fact"><strong>Travel budget:</strong> {draftRequest.travel_budget_rupees != null ? `₹${draftRequest.travel_budget_rupees}` : "Not specified"}</p>
          <p className="fact"><strong>Care budget:</strong> {draftRequest.care_budget_rupees != null ? `₹${draftRequest.care_budget_rupees}` : "Not specified"}</p>
        </div>
      </details>
      <p className="hint">{tx(language, "confirm_caption")}</p>

      <div className="btn-row">
        <button className="btn" onClick={() => navigate("/intake")}>
          {tx(language, "confirm_edit")}
        </button>
        <button className="btn btn-primary" onClick={confirmAndPlan} disabled={loading}>
          {loading && <span className="spinner" />} {tx(language, "confirm_go")}
        </button>
      </div>

      {planResponse && planResponse.safety_branch !== "proceed" && (
        <SafetyBranch response={planResponse} getCopy={get} />
      )}
    </div>
  );
}

function SafetyBranch({ response, getCopy }: { response: PlanResponse; getCopy: (key: GovernedKey) => string }) {
  if (response.safety_branch === "emergency") {
    return <EmergencyPanel onRestart={() => window.location.assign("/intake")} />;
  }
  if (response.safety_branch === "confirm_care_setting") {
    return (
      <div className="alert alert-warning">
        <p>{response.message}</p>
        <p className="hint">{getCopy("confirm_care_setting_help")}</p>
      </div>
    );
  }
  if (response.safety_branch === "incomplete_intake") {
    return (
      <div className="alert alert-error">
        <p>{response.message}</p>
        <ul>
          {response.validation_errors.map((err) => (
            <li key={err}>{err}</li>
          ))}
        </ul>
        <p className="hint">Choose “Edit request” to complete the missing details.</p>
      </div>
    );
  }
  return null;
}
