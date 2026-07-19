// Read-only display helpers ported from src/enrichment.py + src/trust.py.
// The enrichment payload itself always arrives already-normalized from the
// backend (src/backend/service.py calls enrichment.normalize before ever
// reaching the API); these functions only decide how to *render* it, exactly
// mirroring the Python module's product rules:
//   * a claim with no evidence span is kept, not dropped, and marked unverified
//   * data_quality is a caution surface, never a reason to suppress a facility
// trust_chip explanations are deliberately left in English, matching
// src/trust.py — that module's `explanation` text was never localized in the
// original app either.

import type { Enrichment, ClaimEntry } from "../api";

export const CLAIM_GROUPS: readonly [key: keyof Enrichment, heading: string][] = [
  ["capabilities", "Capabilities"],
  ["procedures", "Procedures"],
  ["equipment", "Equipment"],
  ["facility_facts", "Facility facts"],
];

export function isEmpty(e: Enrichment): boolean {
  return (
    !e.capabilities.length &&
    !e.procedures.length &&
    !e.equipment.length &&
    !e.facility_facts.length &&
    !e.specialties.length
  );
}

export interface ClaimRow {
  heading: string;
  text: string;
  evidence: string[];
  verified: boolean;
}

export function iterClaims(e: Enrichment): ClaimRow[] {
  const rows: ClaimRow[] = [];
  for (const [key, heading] of CLAIM_GROUPS) {
    const entries = e[key] as ClaimEntry[];
    for (const entry of entries) {
      rows.push({ heading, text: (entry.claim ?? entry.fact ?? "") as string, evidence: entry.evidence, verified: entry.verified });
    }
  }
  return rows;
}

export function unverifiedCount(e: Enrichment): number {
  return iterClaims(e).filter((row) => !row.verified).length;
}

export function cautions(e: Enrichment): string[] {
  const quality = e.data_quality;
  const lines: string[] = [];
  if (quality.conflicting_claims.length) {
    lines.push(
      `${quality.conflicting_claims.length} detail(s) in this facility's records disagree with each other — call before travelling.`,
    );
  }
  if (quality.possible_merged_facility) {
    lines.push(
      "These records may describe more than one facility merged into a single entry" +
        (quality.merge_suspicion_reason ? `: ${quality.merge_suspicion_reason}` : "."),
    );
  }
  if (!quality.has_rich_description) {
    lines.push("This facility's record is sparse, so little could be extracted. That is missing information, not missing services.");
  }
  return lines;
}

export type TrustLevel = "not_established" | "weak" | "supported" | "strong" | "conflicting";

export interface TrustAssessment {
  trust_level: TrustLevel;
  explanation: string;
  missing_fields: string[];
}

export function assessRecord(e: Enrichment): TrustAssessment {
  const quality = e.data_quality;
  const receipts: { field: string; row: string; span: string }[] = [];
  const seen = new Set<string>();
  for (const [key, heading] of CLAIM_GROUPS) {
    const entries = e[key] as ClaimEntry[];
    const groupText = entries.flatMap((entry) => entry.evidence).join(" ");
    for (const entry of entries) {
      for (const span of entry.evidence) {
        const field = heading.trim();
        const spanTrim = span.trim();
        if (!field || !groupText.trim() || !spanTrim) continue;
        if (!groupText.toLowerCase().includes(spanTrim.toLowerCase())) continue;
        const dedupeKey = `${field.toLowerCase()}|${spanTrim.toLowerCase()}`;
        if (seen.has(dedupeKey)) continue;
        seen.add(dedupeKey);
        receipts.push({ field, row: "row not documented", span: spanTrim });
      }
    }
  }

  const fields = Array.from(new Set(receipts.map((r) => r.field)));
  const fieldKeysLower = new Set(fields.map((f) => f.toLowerCase()));
  const conflictNotes = Array.from(new Set(quality.conflicting_claims.map((c) => c.trim()).filter(Boolean)));
  const expectedHeadings = CLAIM_GROUPS.map(([, heading]) => heading);
  const missing = Array.from(new Set(expectedHeadings.filter((h) => !fieldKeysLower.has(h.toLowerCase()))));

  let trust_level: TrustLevel;
  let explanation: string;
  if (conflictNotes.length) {
    trust_level = "conflicting";
    explanation = `${fields.length} distinct source field(s) contain literal evidence, but conflicting source information must be resolved.`;
  } else if (receipts.length === 0) {
    trust_level = "not_established";
    explanation = "No verified literal evidence establishes this claim in the source record.";
  } else if (fields.length >= 3) {
    trust_level = "strong";
    explanation = "Literal evidence is corroborated across at least three distinct source fields.";
  } else if (fields.length === 2) {
    trust_level = "supported";
    explanation = "Literal evidence is corroborated across two distinct source fields.";
  } else {
    trust_level = "weak";
    explanation = "Literal evidence appears in one source field and should be double-checked.";
  }

  return { trust_level, explanation, missing_fields: missing };
}
