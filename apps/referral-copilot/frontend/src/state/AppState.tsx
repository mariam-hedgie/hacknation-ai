import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, type PersistedPlan, type PlanOption, type PlanRequestBody, type PlanResponse, type Profile } from "../api";
import type { LangCode } from "../i18n/copy";

function emptyProfile(): Profile {
  return { name: "", email: "", history: [], saved: [], ratings: {}, blocklist: [] };
}

function savedFromPersisted(plan: PersistedPlan) {
  const option = plan.selected_option ?? {};
  return {
    plan_id: plan.plan_id,
    facility: String(option.facility ?? "Saved facility"),
    label: String(option.label ?? "Saved route"),
    care_task: String(option.care_task ?? "known_referral"),
    travel: option.travel ? String(option.travel) : undefined,
    cost: option.cost ? String(option.cost) : undefined,
    next_step: option.next_step ? String(option.next_step) : plan.next_steps?.[0],
    unknowns: option.unknowns ? String(option.unknowns) : undefined,
    evidence_status: option.evidence_status ? String(option.evidence_status) : undefined,
  };
}

interface User { name: string }

interface AppStateValue {
  language: LangCode;
  setLanguage: (lang: LangCode) => void;
  user: User | null;
  profile: Profile;
  isLoggedIn: boolean;
  persistenceMode: "lakebase" | "local_demo" | "unavailable";
  persistenceError: string;
  persistProfile: (next: Profile) => void;
  savedPlans: PlanOption[];
  saveOption: (option: PlanOption, careTask: string, note?: string) => Promise<boolean>;
  deleteSavedPlan: (planId: string) => Promise<void>;
  feedback: { status: string; note: string } | null;
  setFeedback: (status: string, note: string) => Promise<boolean>;
  careTask: string;
  setCareTask: (task: string) => void;
  emergencyReported: boolean;
  setEmergencyReported: (v: boolean) => void;
  draftRequest: PlanRequestBody | null;
  setDraftRequest: (req: PlanRequestBody | null) => void;
  planResponse: PlanResponse | null;
  setPlanResponse: (res: PlanResponse | null) => void;
}

const AppStateContext = createContext<AppStateValue | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<LangCode>(() => (localStorage.getItem("aven_language") as LangCode) || "en");
  const [user, setUser] = useState<User | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [profile, setProfile] = useState<Profile>(emptyProfile());
  const [savedPlans, setSavedPlans] = useState<PlanOption[]>([]);
  const [persistenceMode, setPersistenceMode] = useState<"lakebase" | "local_demo" | "unavailable">("unavailable");
  const [persistenceError, setPersistenceError] = useState("");
  const [lastSavedPlanId, setLastSavedPlanId] = useState<string | null>(null);
  const [feedback, setFeedbackState] = useState<{ status: string; note: string } | null>(null);
  const [careTask, setCareTask] = useState("known_referral");
  const [emergencyReported, setEmergencyReported] = useState(false);
  const [draftRequest, setDraftRequest] = useState<PlanRequestBody | null>(null);
  const [planResponse, setPlanResponse] = useState<PlanResponse | null>(null);

  useEffect(() => { localStorage.setItem("aven_language", language); }, [language]);

  useEffect(() => {
    Promise.all([api.session(), api.listPlans()])
      .then(([session, saved]) => {
        setUser({ name: session.display_name });
        setAuthenticated(session.authenticated);
        setPersistenceMode(saved.persistence);
        setProfile((current) => ({ ...current, saved: saved.plans.map(savedFromPersisted) }));
        setPersistenceError("");
      })
      .catch(() => {
        setPersistenceMode("unavailable");
        setPersistenceError("Saved plans are unavailable until secure persistence is configured.");
      });
  }, []);

  const setLanguage = useCallback((lang: LangCode) => setLanguageState(lang), []);
  const persistProfile = useCallback((next: Profile) => setProfile(next), []);

  const saveOption = useCallback(async (option: PlanOption, selectedCareTask: string, note = "") => {
    const existing = profile.saved.find((item) => item.facility === option.facility);
    if (existing) return true;
    const planId = `plan-${crypto.randomUUID()}`;
    try {
      const response = await api.savePlan({
        plan_id: planId,
        selected_facility_id: option.facility,
        selected_option: {
          facility: option.facility,
          label: option.label,
          care_task: selectedCareTask,
          travel: option.travel,
          cost: option.cost,
          evidence: option.evidence,
          evidence_status: option.evidence_status,
          unknowns: option.unknowns,
          next_step: option.next_step,
          ranking: option.ranking,
        },
        next_steps: [option.next_step],
        user_override: note.trim() ? { facility_id: option.facility, note: note.trim(), selected_despite_rank: true } : undefined,
      });
      setPersistenceMode(response.persistence);
      setSavedPlans((current) => current.some((item) => item.facility === option.facility) ? current : [...current, option]);
      setProfile((current) => ({ ...current, saved: [savedFromPersisted(response.plan), ...current.saved] }));
      setLastSavedPlanId(planId);
      setPersistenceError("");
      return true;
    } catch {
      setPersistenceError("This plan was not saved. Secure persistence did not confirm the write.");
      return false;
    }
  }, [profile.saved]);

  const deleteSavedPlan = useCallback(async (planId: string) => {
    const response = await api.deletePlan(planId);
    if (response.deleted) setProfile((current) => ({ ...current, saved: current.saved.filter((item) => item.plan_id !== planId) }));
  }, []);

  const setFeedback = useCallback(async (status: string, note: string) => {
    if (!lastSavedPlanId) {
      setPersistenceError("Save a plan before attaching outcome feedback.");
      return false;
    }
    try {
      await api.saveFeedback(lastSavedPlanId, status, note);
      setFeedbackState({ status, note });
      return true;
    } catch {
      setPersistenceError("Feedback was not saved. Try again after reopening the plan.");
      return false;
    }
  }, [lastSavedPlanId]);

  const value = useMemo<AppStateValue>(() => ({
    language, setLanguage, user, profile, isLoggedIn: authenticated, persistenceMode, persistenceError,
    persistProfile, savedPlans, saveOption, deleteSavedPlan, feedback, setFeedback, careTask, setCareTask,
    emergencyReported, setEmergencyReported, draftRequest, setDraftRequest, planResponse, setPlanResponse,
  }), [language, setLanguage, user, profile, authenticated, persistenceMode, persistenceError, persistProfile, savedPlans, saveOption, deleteSavedPlan, feedback, setFeedback, careTask, emergencyReported, draftRequest, planResponse]);

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState(): AppStateValue {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}

export function addHistory(profile: Profile, request: { care_task: string; capability: string; location: string }): Profile {
  const entry = { ts: Date.now() / 1000, care_task: request.care_task, capability: request.capability, location: request.location };
  return { ...profile, history: [entry, ...profile.history].slice(0, 40) };
}

export function blockFacility(profile: Profile, facility: string): Profile {
  if (profile.blocklist.includes(facility)) return profile;
  return { ...profile, blocklist: [...profile.blocklist, facility] };
}

export function unblockFacility(profile: Profile, facility: string): Profile {
  return { ...profile, blocklist: profile.blocklist.filter((item) => item !== facility) };
}

export function isBlocked(profile: Profile, facility: string): boolean {
  return profile.blocklist.includes(facility);
}
