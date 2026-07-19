import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import { FEATURE_TILES_EN, LANGUAGE_FALLBACK, tileCopy, type LangCode } from "../i18n/copy";
import { LogoPulse } from "./Icons";

export function Header() {
  const navigate = useNavigate();
  const { language, setLanguage, user, isLoggedIn, login, logout, savedPlans } = useAppState();
  const [formsOpen, setFormsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loginError, setLoginError] = useState("");

  const goIntake = (careTask?: string) => {
    setFormsOpen(false);
    navigate("/intake", { state: { careTask } });
  };

  const handleLogin = async () => {
    if (!email.trim()) {
      setLoginError("Enter an email to log in, or just close this and continue as a guest.");
      return;
    }
    await login(name, email);
    setAccountOpen(false);
    setLoginError("");
  };

  return (
    <header className="header">
      <div className="header-inner">
        <button className="brand" onClick={() => navigate("/")}>
          <LogoPulse />
          Aven
        </button>
        <button className="nav-link" onClick={() => navigate("/")}>
          Home
        </button>
        <div className="popover-wrap">
          <button className="nav-link" onClick={() => setFormsOpen((v) => !v)}>
            Forms
          </button>
          {formsOpen && (
            <div className="popover-panel" onMouseLeave={() => setFormsOpen(false)}>
              <h4>Choose a form</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {FEATURE_TILES_EN.map((tile) => {
                  const copy = tileCopy(language, tile.key);
                  return (
                    <button
                      key={tile.key}
                      className="btn"
                      style={{ justifyContent: "flex-start", textTransform: "none", letterSpacing: 0 }}
                      onClick={() => goIntake(tile.key)}
                    >
                      {tile.icon} {copy.title}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
        <button className="nav-link" onClick={() => navigate("/ask")}>
          Ask
        </button>
        {savedPlans.length > 0 && (
          <button className="nav-link" onClick={() => navigate("/results")}>
            Saved
          </button>
        )}
        <div className="header-spacer" />
        <select
          className="lang-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value as LangCode)}
          aria-label="Language"
        >
          {Object.entries(LANGUAGE_FALLBACK).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
        <div className="popover-wrap">
          <button className="nav-link" onClick={() => setAccountOpen((v) => !v)}>
            {isLoggedIn ? `👤 ${(user!.name.split(" ")[0]) || "Member"}` : "Log in"}
          </button>
          {accountOpen && (
            <div className="popover-panel">
              {isLoggedIn ? (
                <>
                  <h4>Signed in · {user!.email}</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    <button
                      className="btn btn-block"
                      onClick={() => {
                        setAccountOpen(false);
                        navigate("/profile");
                      }}
                    >
                      My profile
                    </button>
                    <button
                      className="btn btn-block"
                      onClick={() => {
                        setAccountOpen(false);
                        logout();
                        navigate("/");
                      }}
                    >
                      Log out
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <h4>Log in to Aven</h4>
                  <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0 0 0.6rem" }}>
                    No account needed — you can submit forms as a guest. Log in to keep your history, hospital
                    ratings, and blocked facilities across visits.
                  </p>
                  <div className="field">
                    <input type="text" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} />
                  </div>
                  <div className="field">
                    <input
                      type="text"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                  {loginError && <div className="alert alert-warning">{loginError}</div>}
                  <button className="btn btn-primary btn-block" onClick={handleLogin}>
                    Log in
                  </button>
                  <button
                    className="btn btn-block"
                    style={{ marginTop: "0.5rem" }}
                    onClick={() => {
                      setAccountOpen(false);
                      navigate("/profile");
                    }}
                  >
                    View my activity (guest)
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
