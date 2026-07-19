import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const exists = (path) => existsSync(new URL(`../${path}`, import.meta.url));

test("the built React bundle is committed so a Python-only host can serve it", () => {
  // dist/ is deliberately committed (see frontend/.gitignore): it lets a plain
  // Python host run the app with no Node toolchain, and stops a Databricks
  // deploy breaking if the npm build step never runs. If this fails, run
  // `npm --prefix apps/referral-copilot run build` and commit the result.
  const dist = "apps/referral-copilot/frontend/dist";
  assert.ok(exists(dist), `${dist} is missing — build and commit it`);

  const html = read(`${dist}/index.html`);
  const referenced = [...html.matchAll(/(?:src|href)="\/(assets\/[^"]+)"/g)].map((m) => m[1]);
  assert.ok(referenced.length > 0, "index.html references no built assets");
  for (const asset of referenced)
    assert.ok(exists(`${dist}/${asset}`), `index.html references missing ${asset}`);
});

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

test("React uses consistent accessible line icons instead of emoji UI glyphs", () => {
  const icons = read("apps/referral-copilot/frontend/src/components/Icons.tsx");
  const app = read("apps/referral-copilot/frontend/src/App.tsx");
  const evidence = read("apps/referral-copilot/frontend/src/components/Evidence.tsx");
  const header = read("apps/referral-copilot/frontend/src/components/Header.tsx");
  const option = read("apps/referral-copilot/frontend/src/components/OptionCard.tsx");
  const landing = read("apps/referral-copilot/frontend/src/pages/Landing.tsx");
  const intake = read("apps/referral-copilot/frontend/src/pages/Intake.tsx");
  const results = read("apps/referral-copilot/frontend/src/pages/Results.tsx");
  const copy = read("apps/referral-copilot/frontend/src/i18n/copy.ts");

  for (const component of [
    "TaskIcon",
    "OptionIcon",
    "EvidenceIcon",
    "IconShield",
    "IconBan",
    "IconMapPin",
    "IconDatabase",
    "IconChevronDown",
  ]) assert.match(icons, new RegExp(`export function ${component}`));
  assert.match(icons, /aria-hidden="true"/);
  assert.match(icons, /focusable="false"/);
  assert.match(app, /<IconShield size=\{16\}/);
  assert.match(evidence, /<EvidenceIcon status=\{status\}/);
  assert.match(header, /<TaskIcon name=\{tile\.key\}/);
  assert.match(option, /<OptionIcon label=\{option\.label\}/);
  assert.match(option, /<IconBan size=\{16\}/);
  assert.match(landing, /<IconChevronDown/);
  assert.match(landing, /<TaskIcon name=\{tile\.key\}/);
  assert.match(intake, /<TaskIcon name=\{careTask\}/);
  assert.match(results, /<OptionIcon label=\{plan\.label\}/);
  assert.doesNotMatch(copy, /OPTION_ICONS/);
  assert.doesNotMatch(copy, /icon:\s*"/);
  for (const source of [app, evidence, header, option, landing, intake, results])
    assert.doesNotMatch(source, /[🛡️✅⚠️❔🔗🗒️🥇🧭🔍📍⚙️🚫]/u);
});
