import { useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import { FEATURE_TILES_EN, STRINGS, tileCopy, tx } from "../i18n/copy";
import { EcgDivider, IconChevronDown, LogoPulse, TaskIcon } from "../components/Icons";
import { Reveal } from "../components/Reveal";

export function Landing() {
  const navigate = useNavigate();
  const { language } = useAppState();
  const strings = STRINGS[language];

  const goIntake = (careTask?: string) => navigate("/intake", { state: { careTask } });

  return (
    <div className="page" style={{ padding: 0 }}>
      <div className="hero-full">
        <div className="hero-inner">
          <span className="eyebrow">
            <LogoPulse />
            {strings.eyebrow}
          </span>
          <h1 className="display">aven</h1>
          <EcgDivider />
          <p className="hero-tagline" dangerouslySetInnerHTML={{ __html: tx(language, "hero_tagline") }} />
          <p className="hero-sub">{tx(language, "hero_sub")}</p>
          <a className="scroll-cue" href="#statement">
            <span>{tx(language, "scroll_cue")}</span>
            <span className="chevron"><IconChevronDown size={18} /></span>
          </a>
        </div>
      </div>

      <div className="marquee" aria-hidden="true">
        <div className="marquee-track">
          {[...tx(language, "marquee"), ...tx(language, "marquee")].map((phrase, i) => (
            <span key={i}>{phrase}</span>
          ))}
        </div>
      </div>

      <div className="page">
        <Reveal>
          <div id="statement" className="statement">
            <span className="section-title">{tx(language, "statement_kicker")}</span>
            <p className="statement-text" dangerouslySetInnerHTML={{ __html: tx(language, "statement") }} />
          </div>
        </Reveal>

        <div className="about">
          <Reveal>
            <span className="section-title">{tx(language, "about_eyebrow")}</span>
            <h2 className="about-title">{tx(language, "about_title")}</h2>
            <p className="about-body">{tx(language, "about_body")}</p>
          </Reveal>
          <div className="about-points">
            {tx(language, "about_points").map(([title, body], i) => (
              <Reveal key={title} delayMs={i * 90}>
                <div className="about-point">
                  <div className="about-point-num">/ 0{i + 1}</div>
                  <h4>{title}</h4>
                  <p>{body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        <Reveal>
          <div className="tiles-head">
            <span className="section-title">{tx(language, "tiles_eyebrow")}</span>
            <h2 className="about-title">{tx(language, "tiles_title")}</h2>
            <p className="tiles-hint">{tx(language, "tiles_hint")}</p>
          </div>
        </Reveal>
        <div className="tiles-grid">
          {FEATURE_TILES_EN.map((tile) => {
            const copy = tileCopy(language, tile.key);
            return (
              <button key={tile.key} className="tile" onClick={() => goIntake(tile.key)}>
                <span className="tile-icon"><TaskIcon name={tile.key} size={26} /></span>
                <span className="tile-title">{copy.title}</span>
                <span className="tile-desc">{copy.desc}</span>
                <span className="tile-cta">{tx(language, "nav_cta")} →</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
