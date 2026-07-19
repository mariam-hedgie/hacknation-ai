// Client-side session state, mirroring app.py's st.session_state usage:
// language/user persist across reloads (localStorage), everything else
// (draft request, plan response, saved plans this session) is in-memory only,
// matching the original per-tab Streamlit session lifetime.

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, type PlanOption, type PlanRequestBody, type PlanResponse, type Profile } from "../api";
import type { LangCode } from "../i18n/copy";

function emptyProfile(email = ""): Profile {
  return { name: "", email, history: [], saved: [], ratings: {}, blocklist: [] };
}

interface User {
  name: string;
  email: string;
}

interface AppStateValue {
  language: LangCode;
  setLanguage: (lang: LangCode) => void;
  user: User | null;
  profile: Profile;
  isLoggedIn: boolean;
  login: (name: string, email: string) => Promise<void>;
  logout: () => void;
  persistProfile: (next: Profile) => void;
  savedPlans: PlanOption[];
  saveOption: (option: PlanOption, careTask: string) => boolean;
  feedback: { status: string; note: string } | null;
  setFeedback: (status: string, note: string) => void;
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
  const [language, setLanguageState] = useState<LangCode>(() => {
    const stored = localStorage.getItem("aven_language");
    return (stored as LangCode) || "en";
  });
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem("aven_user");
    return stored ? (JSON.parse(stored) as User) : null;
  });
  const [profile, setProfile] = useState<Profile>(emptyProfile());
  const [savedPlans, setSavedPlans] = useState<PlanOption[]>([]);
  const [feedback, setFeedbackState] = useState<{ status: string; note: string } | null>(null);
  const [careTask, setCareTask] = useState<string>("known_referral");
  const [emergencyReported, setEmergencyReported] = useState(false);
  const [draftRequest, setDraftRequest] = useState<PlanRequestBody | null>(null);
  const [planResponse, setPlanResponse] = useState<PlanResponse | null>(null);

  useEffect(() => {
    localStorage.setItem("aven_language", language);
  }, [language]);

  useEffect(() => {
    if (user) {
      localStorage.setItem("aven_user", JSON.stringify(user));
      api.getProfile(user.email).then(setProfile).catch(() => {});
    } else {
      localStorage.removeItem("aven_user");
    }
  }, [user]);

  const setLanguage = useCallback((lang: LangCode) => setLanguageState(lang), []);

  const login = useCallback(async (name: string, email: string) => {
    const trimmedEmail = email.trim();
    const loaded = await api.getProfile(trimmedEmail);
    if (name.trim()) loaded.name = name.trim();
    loaded.email = trimmedEmail;
    setProfile(loaded);
    setUser({ name: loaded.name || "Member", email: trimmedEmail });
    await api.saveProfile(loaded);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setProfile(emptyProfile());
  }, []);

  const persistProfile = useCallback(
    (next: Profile) => {
      setProfile(next);
      if (user) api.saveProfile(next).catch(() => {});
    },
    [user],
  );

  const saveOption = useCallback(
    (option: PlanOption, careTask: string) => {
      const alreadySaved = savedPlans.some((p) => p.facility === option.facility);
      setSavedPlans((prev) => [...prev, option]);
      if (!profile.saved.some((item) => item.facility === option.facility)) {
        const next: Profile = {
          ...profile,
          saved: [{ facility: option.facility, label: option.label, care_task: careTask }, ...profile.saved],
        };
        persistProfile(next);
      }
      return !alreadySaved;
    },
    [savedPlans, profile, persistProfile],
  );

  const setFeedback = useCallback((status: string, note: string) => setFeedbackState({ status, note }), []);

  const value = useMemo<AppStateValue>(
    () => ({
      language,
      setLanguage,
      user,
      profile,
      isLoggedIn: user !== null,
      login,
      logout,
      persistProfile,
      savedPlans,
      saveOption,
      feedback,
      setFeedback,
      careTask,
      setCareTask,
      emergencyReported,
      setEmergencyReported,
      draftRequest,
      setDraftRequest,
      planResponse,
      setPlanResponse,
    }),
    [
      language,
      setLanguage,
      user,
      profile,
      login,
      logout,
      persistProfile,
      savedPlans,
      saveOption,
      feedback,
      setFeedback,
      careTask,
      emergencyReported,
      draftRequest,
      planResponse,
    ],
  );

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

export function setRating(profile: Profile, facility: string, rating: number): Profile {
  return { ...profile, ratings: { ...profile.ratings, [facility]: { rating, note: "" } } };
}

export function getRating(profile: Profile, facility: string): number | null {
  return profile.ratings[facility]?.rating ?? null;
}

export function blockFacility(profile: Profile, facility: string): Profile {
  if (profile.blocklist.includes(facility)) return profile;
  return { ...profile, blocklist: [...profile.blocklist, facility] };
}

export function unblockFacility(profile: Profile, facility: string): Profile {
  return { ...profile, blocklist: profile.blocklist.filter((f) => f !== facility) };
}

export function isBlocked(profile: Profile, facility: string): boolean {
  return profile.blocklist.includes(facility);
}
