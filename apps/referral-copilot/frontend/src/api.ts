// Thin fetch client for the local Aven API (src/backend/api.py). Every call
// here maps 1:1 to an existing, framework-independent Python function — no
// business logic is duplicated in the frontend.

const BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? "http://127.0.0.1:8010" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${init?.method ?? "GET"} ${path} failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

export interface CopyResult {
  text: string;
  language: string;
  used_fallback: boolean;
  fallback_message: string | null;
}

export interface ServiceStatus {
  map_provider: string;
  map_live_provider: boolean;
  voice_available: boolean;
  voice_message: string;
  databricks_mode: string;
  backend_mode: string;
  tools: Record<string, boolean>;
}

export interface TravelCapability {
  mode: string;
  provider: string;
  route_supported: boolean;
  comparison_only: boolean;
  live_price_supported: boolean;
  live_transit_supported: boolean;
  label: string;
}

export interface ClaimEntry {
  claim?: string;
  fact?: string;
  evidence: string[];
  verified: boolean;
}

export interface Enrichment {
  capabilities: ClaimEntry[];
  procedures: ClaimEntry[];
  equipment: ClaimEntry[];
  facility_facts: ClaimEntry[];
  specialties: string[];
  data_quality: {
    has_rich_description: boolean;
    conflicting_claims: string[];
    possible_merged_facility: boolean;
    merge_suspicion_reason: string | null;
  };
}

export interface PlanOption {
  label: string;
  facility: string;
  summary: string;
  travel: string;
  cost: string;
  evidence: string;
  unknowns: string;
  next_step: string;
  ranking: string;
  evidence_status?: string;
  distance_km?: number | null;
  recommended_mode?: string | null;
  estimated_journey_minutes?: number | null;
  estimated_travel_cost_rupees?: number | null;
  arrival_feasible?: boolean | null;
  ambulance_documented?: boolean;
  enrichment: Enrichment;
}

export interface PlanRequestBody {
  message?: string | null;
  care_task: string;
  capability?: string | null;
  location?: string | null;
  urgency: string;
  travel_tolerance: string;
  budget_sensitivity: string;
  facility_preference: string;
  language?: string | null;
  medication_name?: string | null;
  has_current_prescription?: boolean | null;
  has_clinician_order?: boolean | null;
  emergency_warning_reported: boolean;
  max_distance_km?: number | null;
  travel_modes?: string[];
  travel_budget_rupees?: number | null;
  care_budget_rupees?: number | null;
  required_arrival_date?: string | null;
}

export interface IntakeDraft {
  care_task: string;
  capability: string | null;
  location: string | null;
  urgency: string;
  travel_modes: string[];
  language: string | null;
  clarification_question: string | null;
  requires_review: boolean;
}

export interface JourneyResult {
  maps_url: string;
  estimate: null | {
    duration_minutes: number;
    cost_low_rupees: number;
    cost_high_rupees: number;
    disclaimer: string;
  };
  ticket_links: { label: string; url: string; external_booking: boolean }[];
}

export interface PublicSourceCandidate {
  title: string;
  url: string;
  snippet: string;
  phone_numbers: string[];
  retrieved_at: string;
  status: string;
}

export interface SavedPlan {
  plan_id?: string;
  facility: string;
  label: string;
  care_task: string;
  travel?: string;
  cost?: string;
  next_step?: string;
  unknowns?: string;
  evidence_status?: string;
  saved_at?: number;
}

export interface PersistedPlan {
  plan_id: string;
  selected_facility_id?: string;
  selected_option?: Partial<PlanOption> & { care_task?: string };
  next_steps?: string[];
  user_override?: { facility_id: string; note: string; selected_despite_rank: boolean };
}

export interface SessionInfo {
  display_name: string;
  authenticated: boolean;
  persistence: "lakebase" | "local_demo";
}

export interface PlanResponse {
  safety_branch: "proceed" | "emergency" | "confirm_care_setting" | "incomplete_intake";
  options: PlanOption[];
  message: string | null;
  validation_errors: string[];
}

export interface AskResult {
  answered: boolean;
  result: {
    answer?: string;
    sql?: string;
    columns?: string[];
    rows?: Record<string, unknown>[];
    conversation_id?: string;
  } | null;
}

export interface Profile {
  name: string;
  email: string;
  history: { ts: number; care_task: string; capability: string; location: string }[];
  saved: SavedPlan[];
  ratings: Record<string, { rating: number; note: string }>;
  blocklist: string[];
}

export const api = {
  languages: () => request<Record<string, string>>("/api/languages"),
  careTasks: () => request<Record<string, string>>("/api/care-tasks"),
  copy: (key: string, language: string) =>
    request<CopyResult>(`/api/copy?key=${encodeURIComponent(key)}&language=${encodeURIComponent(language)}`),
  serviceStatus: () => request<ServiceStatus>("/api/service-status"),
  travelCapabilities: (modes: string[]) =>
    request<TravelCapability[]>(`/api/travel-capabilities?modes=${encodeURIComponent(modes.join(","))}`),
  plan: (body: PlanRequestBody) =>
    request<PlanResponse>("/api/plan", { method: "POST", body: JSON.stringify(body) }),
  structureIntake: (text: string) =>
    request<IntakeDraft>("/api/structure-intake", { method: "POST", body: JSON.stringify({ text }) }),
  transcribe: (audio_base64: string, language_code: string) =>
    request<{ text: string; requires_review: boolean }>("/api/transcribe", {
      method: "POST",
      body: JSON.stringify({ audio_base64, language_code }),
    }),
  journey: (origin: string, destination: string, mode: string, distance_km: number | null) =>
    request<JourneyResult>("/api/journey", {
      method: "POST",
      body: JSON.stringify({ origin, destination, mode, distance_km }),
    }),
  publicSources: (facility: string, capability: string) =>
    request<{ candidates: PublicSourceCandidate[] }>("/api/public-sources", {
      method: "POST",
      body: JSON.stringify({ facility, capability }),
    }),
  ask: (question: string, conversation_id: string | null) =>
    request<AskResult>("/api/ask", { method: "POST", body: JSON.stringify({ question, conversation_id }) }),
  session: () => request<SessionInfo>("/api/session"),
  listPlans: () => request<{ persistence: "lakebase" | "local_demo"; plans: PersistedPlan[] }>("/api/plans"),
  savePlan: (plan: PersistedPlan) =>
    request<{ persistence: "lakebase" | "local_demo"; plan: PersistedPlan }>("/api/plans", {
      method: "POST",
      body: JSON.stringify(plan),
    }),
  saveFeedback: (planId: string, status: string, note: string) =>
    request<{ feedback: { plan_id: string; status: string; note: string } }>(`/api/plans/${encodeURIComponent(planId)}/feedback`, {
      method: "POST",
      body: JSON.stringify({ status, note }),
    }),
  deletePlan: (planId: string) =>
    request<{ deleted: boolean }>(`/api/plans/${encodeURIComponent(planId)}`, { method: "DELETE" }),
};
