import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import { FEATURE_TILES_EN, LANGUAGE_FALLBACK, tileCopy, type LangCode } from "../i18n/copy";
import { LogoPulse } from "./Icons";

export function Header() {
  const navigate = useNavigate();
  const { language, setLanguage, user, isLoggedIn, persistenceMode, savedPlans, profile } = useAppState();
  const [formsOpen, setFormsOpen] = useState(false);

  const goIntake = (careTask?: string) => {
    setFormsOpen(false);
    navigate("/intake", { state: { careTask } });
  };

  return (
    <header className="header">
      <div className="header-inner">
        <button className="brand" onClick={() => navigate("/")}>
          <LogoPulse />
          aven
        </button>
        <button className="nav-link" onClick={() => navigate("/")}>
          Home
        </button>
        <div className="popover-wrap">
          <button className="nav-link" onClick={() => setFormsOpen((v) => !v)}>
            Plan care
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
          Quick lookup
        </button>
        <button className="nav-link" onClick={() => navigate("/profile")}>
          My plans ({Math.max(savedPlans.length, profile.saved.length)})
        </button>
        <button className="nav-link emergency-nav" onClick={() => navigate("/intake", { state: { careTask: "symptom_first", emergency: true } })}>
          Emergency help
        </button>
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
        <span className="session-chip" title={isLoggedIn ? "Authenticated by Databricks" : "Local demo only"}>
          {user?.name || "Connecting…"} · {persistenceMode === "lakebase" ? "saved securely" : "local demo"}
        </span>
      </div>
    </header>
  );
}
