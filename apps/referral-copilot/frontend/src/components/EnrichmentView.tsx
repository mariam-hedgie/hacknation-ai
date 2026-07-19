import type { Enrichment } from "../api";
import { assessRecord, cautions, iterClaims, isEmpty, unverifiedCount } from "../lib/enrichment";
import { Chips, QualityNote, TrustChip } from "./Evidence";
import { TRUST_LEVEL_KEYS, useGovernedCopy } from "../i18n/governed";

export function EnrichmentView({ enrichment }: { enrichment: Enrichment }) {
  const { get } = useGovernedCopy();
  const assessment = assessRecord(enrichment);
  const cautionLines = cautions(enrichment);
  const claims = iterClaims(enrichment);
  const unverified = unverifiedCount(enrichment);

  if (isEmpty(enrichment)) {
    return (
      <>
        <p className="fact" style={{ fontStyle: "italic" }}>
          Nothing could be extracted from this facility's record yet. Confirm services by phone.
        </p>
      </>
    );
  }

  let currentHeading: string | null = null;

  return (
    <>
      <Chips labels={enrichment.specialties} />
      <TrustChip label={get(TRUST_LEVEL_KEYS[assessment.trust_level])} explanation={assessment.explanation} />
      {cautionLines.map((line, i) => (
        <QualityNote key={i} text={line} sparse={line.startsWith("This facility's record is sparse")} />
      ))}

      <details className="disclosure">
        <summary>
          What the records say
          {unverified ? ` · ${unverified} claim(s) without a source span` : ""}
        </summary>
        <div>
          {claims.map((row, i) => {
            const showHeading = row.heading !== currentHeading;
            currentHeading = row.heading;
            return (
              <div key={i}>
                {showHeading && <div className="claim-group">{row.heading}</div>}
                <div className="claim">
                  <p className="claim-text">
                    {row.text}
                    {!row.verified && <span className="claim-unverified">no source span</span>}
                  </p>
                  {row.evidence.map((span, j) => (
                    <p className="claim-evidence" key={j}>
                      “{span}”
                    </p>
                  ))}
                </div>
              </div>
            );
          })}

          {enrichment.data_quality.conflicting_claims.length > 0 && (
            <>
              <div className="claim-group">Conflicting details</div>
              {enrichment.data_quality.conflicting_claims.map((conflict, i) => (
                <div className="claim" key={i}>
                  <p className="claim-text">{conflict}</p>
                </div>
              ))}
            </>
          )}

          {assessment.missing_fields.length > 0 && (
            <>
              <div className="claim-group">{get("what_we_could_not_confirm")}</div>
              {assessment.missing_fields.map((field) => (
                <QualityNote key={field} text={field} sparse />
              ))}
            </>
          )}
        </div>
      </details>
    </>
  );
}
