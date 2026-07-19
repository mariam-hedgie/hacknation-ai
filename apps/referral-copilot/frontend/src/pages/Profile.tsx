import { useNavigate } from "react-router-dom";
import { useAppState, getRating, setRating, unblockFacility } from "../state/AppState";
import { CARE_TASKS_EN } from "../i18n/copy";

function Stars({ value, onChange }: { value: number | null; onChange: (rating: number) => void }) {
  return (
    <div className="stars">
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} className={`star-btn ${value && n <= value ? "filled" : ""}`} onClick={() => onChange(n)}>
          ★
        </button>
      ))}
    </div>
  );
}

export function Profile() {
  const navigate = useNavigate();
  const { user, isLoggedIn, profile, persistProfile } = useAppState();

  const who = isLoggedIn ? user!.name : "Guest";

  return (
    <div className="page flow-page">
      <div className="profile-head">
        <span className="section-title">Your profile</span>
        <h2 className="about-title">Hello, {who}.</h2>
      </div>
      {!isLoggedIn && (
        <div className="alert alert-info">
          You're browsing as a guest. Log in (top-right) to keep your history, ratings, and blocked facilities across
          visits.
        </div>
      )}

      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{profile.history.length}</div>
          <div className="stat-label">Requests made</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{profile.saved.length}</div>
          <div className="stat-label">Saved referrals</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{profile.blocklist.length}</div>
          <div className="stat-label">Blocked facilities</div>
        </div>
      </div>

      <button className="btn btn-primary" onClick={() => navigate("/intake")}>
        ＋ Start a new request
      </button>

      <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>
        Facilities you blocked
      </div>
      {profile.blocklist.length ? (
        <>
          <p className="hint">Aven will never include these in your routes. Remove one to allow it again.</p>
          {profile.blocklist.map((facility) => (
            <div key={facility} className="history-row" style={{ justifyContent: "space-between" }}>
              <span>🚫 <strong>{facility}</strong></span>
              <button className="btn" onClick={() => persistProfile(unblockFacility(profile, facility))}>
                Unblock
              </button>
            </div>
          ))}
        </>
      ) : (
        <p className="hint">None yet. On any result you can tap “Never refer me here”.</p>
      )}

      <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>
        Saved referrals & ratings
      </div>
      {profile.saved.length ? (
        profile.saved.map((item, i) => {
          const rating = getRating(profile, item.facility);
          const blocked = profile.blocklist.includes(item.facility);
          return (
            <div className="profile-card" key={i}>
              <p className="facility-name" style={{ fontSize: "1.1rem" }}>
                {item.facility}
              </p>
              <p className="fact">
                {CARE_TASKS_EN[item.care_task] ?? "Saved route"} · {item.label}
              </p>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.6rem" }}>
                <div>
                  <p className="hint" style={{ margin: "0 0 0.2rem" }}>
                    Rate this hospital
                  </p>
                  <Stars value={rating} onChange={(r) => persistProfile(setRating(profile, item.facility, r))} />
                </div>
                {blocked ? (
                  <button className="btn" onClick={() => persistProfile(unblockFacility(profile, item.facility))}>
                    Unblock
                  </button>
                ) : (
                  <button
                    className="btn"
                    onClick={() => persistProfile({ ...profile, blocklist: [...profile.blocklist, item.facility] })}
                  >
                    🚫 Never again
                  </button>
                )}
              </div>
            </div>
          );
        })
      ) : (
        <p className="hint">No saved referrals yet. Save a route from your results to rate it later.</p>
      )}

      <div className="section-title" style={{ margin: "2rem 0 0.8rem" }}>
        Past requests
      </div>
      {profile.history.length ? (
        profile.history.map((entry, i) => (
          <div className="history-row" key={i}>
            <span className="history-when">{new Date(entry.ts * 1000).toLocaleString()}</span>
            <span>
              <strong>{CARE_TASKS_EN[entry.care_task] ?? "Request"}</strong> — {entry.capability}{" "}
              <span className="dim">· from {entry.location}</span>
            </span>
          </div>
        ))
      ) : (
        <p className="hint">Nothing here yet. Your submitted requests will show up here.</p>
      )}
    </div>
  );
}
