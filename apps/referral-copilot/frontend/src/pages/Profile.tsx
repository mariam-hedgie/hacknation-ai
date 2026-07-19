import { useNavigate } from "react-router-dom";
import { useAppState, unblockFacility } from "../state/AppState";
import { CARE_TASKS_EN } from "../i18n/copy";

export function Profile() {
  const navigate = useNavigate();
  const { user, isLoggedIn, profile, persistProfile, persistenceMode, persistenceError, deleteSavedPlan } = useAppState();

  return (
    <div className="page flow-page">
      <div className="profile-head">
        <span className="section-title">My plans</span>
        <h2 className="about-title">{user?.name ? `Hello, ${user.name}.` : "Your saved decisions"}</h2>
      </div>

      <div className={`alert ${persistenceMode === "lakebase" ? "alert-success" : "alert-info"}`}>
        {persistenceMode === "lakebase"
          ? "Databricks authenticated you and Lakebase stores only your selected decision and optional note for 30 days."
          : "Local demo mode: plans can survive a browser refresh while this server is running, but this is not proof of Lakebase persistence."}
        {!isLoggedIn && " The deployed app uses Databricks login automatically—aven never asks for a separate password."}
      </div>
      {persistenceError && <div className="alert alert-warning">{persistenceError}</div>}

      <div className="stat-row">
        <div className="stat-card"><div className="stat-value">{profile.saved.length}</div><div className="stat-label">Saved plans</div></div>
        <div className="stat-card"><div className="stat-value">{profile.history.length}</div><div className="stat-label">Requests this session</div></div>
      </div>

      <button className="btn btn-primary" onClick={() => navigate("/intake")}>Start a new request</button>

      <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>Saved decisions</div>
      {profile.saved.length ? profile.saved.map((item) => (
        <div className="profile-card" key={item.plan_id || item.facility}>
          <p className="facility-name" style={{ fontSize: "1.1rem" }}>{item.facility}</p>
          <p className="fact">{CARE_TASKS_EN[item.care_task] ?? "Saved route"} · {item.label}</p>
          {item.travel && <p className="fact"><strong>Journey:</strong> {item.travel}</p>}
          {item.cost && <p className="fact"><strong>Cost:</strong> {item.cost}</p>}
          {item.next_step && <p className="fact"><strong>Next step:</strong> {item.next_step}</p>}
          {item.unknowns && <p className="hint"><strong>Still verify:</strong> {item.unknowns}</p>}
          {item.plan_id && <button className="btn" onClick={() => void deleteSavedPlan(item.plan_id!)}>Delete saved plan</button>}
        </div>
      )) : <p className="hint">No saved plans yet. Save an option only after you have reviewed its evidence and unknowns.</p>}

      {profile.blocklist.length > 0 && (
        <details className="disclosure">
          <summary>Facilities hidden for this session</summary>
          <p className="hint">These preferences stay in this browser session and are not turned into facility evidence.</p>
          {profile.blocklist.map((facility) => (
            <div key={facility} className="history-row" style={{ justifyContent: "space-between" }}>
              <strong>{facility}</strong>
              <button className="btn" onClick={() => persistProfile(unblockFacility(profile, facility))}>Show again</button>
            </div>
          ))}
        </details>
      )}

      <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>Requests this session</div>
      {profile.history.length ? profile.history.map((entry, index) => (
        <div className="history-row" key={index}>
          <span className="history-when">{new Date(entry.ts * 1000).toLocaleString()}</span>
          <span><strong>{CARE_TASKS_EN[entry.care_task] ?? "Request"}</strong> — {entry.capability} <span className="dim">· from {entry.location}</span></span>
        </div>
      )) : <p className="hint">Nothing here yet. Health intake stays in this session and is not written to Lakebase.</p>}
    </div>
  );
}
