import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("React request preserves the complete journey intake contract", () => {
  const api = read("apps/referral-copilot/frontend/src/api.ts");
  const backend = read("apps/referral-copilot/src/backend/api.py");
  for (const field of [
    "max_distance_km",
    "travel_modes",
    "travel_budget_rupees",
    "care_budget_rupees",
    "required_arrival_date",
  ]) {
    assert.match(api, new RegExp(field));
    assert.match(backend, new RegExp(field));
  }
});

test("React exposes the consolidated planning actions", () => {
  const intake = read("apps/referral-copilot/frontend/src/pages/Intake.tsx");
  const journey = read("apps/referral-copilot/frontend/src/components/JourneyPanel.tsx");
  const backend = read("apps/referral-copilot/src/backend/api.py");
  assert.match(intake, /Structure with OpenAI/);
  assert.match(intake, /Required arrival date/);
  assert.match(intake, /Travel modes/);
  assert.match(intake, /Transcribe for review/);
  assert.match(journey, /Open route in Google Maps/);
  assert.match(journey, /Check public contact sources/);
  assert.match(journey, /Call 112/);
  for (const endpoint of ["/api/structure-intake", "/api/journey", "/api/public-sources"])
    assert.match(backend, new RegExp(endpoint));
  assert.match(backend, /\/api\/transcribe/);
});

test("React always exposes lowercase aven and My plans", () => {
  const header = read("apps/referral-copilot/frontend/src/components/Header.tsx");
  assert.match(header, />\s*aven\s*</);
  assert.match(header, /My plans/);
  assert.doesNotMatch(header, />\s*Aven\s*</);
});

test("Databricks deploy builds React and serves it through the authenticated API", () => {
  const appYaml = read("apps/referral-copilot/app.yaml");
  const packageJson = read("apps/referral-copilot/package.json");
  const backend = read("apps/referral-copilot/src/backend/api.py");
  const persistence = read("apps/referral-copilot/src/backend/lakebase.py");
  assert.match(appYaml, /run_app\.py/);
  assert.match(appYaml, /valueFrom: postgres/);
  assert.match(appYaml, /valueFrom: identity-pepper/);
  assert.match(packageJson, /frontend/);
  assert.match(backend, /\/api\/plans/);
  assert.match(persistence, /resolve_identity/);
  assert.match(persistence, /PersistentSqlPlanStore/);
  assert.doesNotMatch(backend, /profile\?email/);
});
