// Governed copy: safety, evidence, and trust wording. These strings must never
// be hardcoded in a view (mirrors the rule in src/localization.py) — they are
// always fetched from the backend's /api/copy, which is a façade over the
// single approved translation table. All keys below are prefetched whenever
// the language changes, so components can read them synchronously.

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
import type { LangCode } from "./copy";

const GOVERNED_KEYS = [
  "review_and_confirm",
  "medical_safety_notice",
  "tell_us",
  "your_plan",
  "call_first",
  "not_confirmed",
  "emergency_title",
  "emergency_body",
  "emergency_restart",
  "confirm_care_setting_help",
  "emergency_intake_warning",
  "emergency_intake_checkbox",
  "evidence_documented",
  "evidence_conflicting",
  "evidence_external",
  "evidence_user_context",
  "what_we_could_not_confirm",
  "trust_strong",
  "trust_supported",
  "trust_weak",
] as const;

export type GovernedKey = (typeof GOVERNED_KEYS)[number];

// EvidenceStatus / trust level -> governed key, mirroring
// src/localization.py's EVIDENCE_STATUS_KEYS / TRUST_LEVEL_KEYS.
export const EVIDENCE_STATUS_KEYS: Record<string, GovernedKey> = {
  documented: "evidence_documented",
  conflicting: "evidence_conflicting",
  not_documented: "not_confirmed",
  external_corroborated: "evidence_external",
  user_context: "evidence_user_context",
};

export const TRUST_LEVEL_KEYS: Record<string, GovernedKey> = {
  strong: "trust_strong",
  supported: "trust_supported",
  weak: "trust_weak",
  not_established: "not_confirmed",
  conflicting: "evidence_conflicting",
};

interface GovernedCopyValue {
  get: (key: GovernedKey) => string;
  ready: boolean;
}

const GovernedCopyContext = createContext<GovernedCopyValue>({ get: (key) => key, ready: false });

export function GovernedCopyProvider({ language, children }: { language: LangCode; children: ReactNode }) {
  const [table, setTable] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setReady(false);
    Promise.all(GOVERNED_KEYS.map((key) => api.copy(key, language).then((r) => [key, r.text] as const)))
      .then((entries) => {
        if (cancelled) return;
        setTable(Object.fromEntries(entries));
        setReady(true);
      })
      .catch(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [language]);

  const value: GovernedCopyValue = {
    get: (key) => table[key] ?? "",
    ready,
  };

  return <GovernedCopyContext.Provider value={value}>{children}</GovernedCopyContext.Provider>;
}

export function useGovernedCopy() {
  return useContext(GovernedCopyContext);
}
