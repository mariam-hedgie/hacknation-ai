# Aven final submission gate

The app is a **GO** only when every required box below contains evidence. Do not
replace a missing check with “code exists.”

## Repository preflight completed

- [x] React production build is served by the same FastAPI host as `/api/*`.
- [x] No browser-supplied owner ID or custom email login is used.
- [x] Databricks proxy identity becomes a pseudonymous owner ID on the server.
- [x] Lakebase uses managed resource coordinates and rotating OAuth database
  credentials; no database password is stored in source or browser state.
- [x] Save/list/delete/feedback queries bind `owner_id`, and persisted JSON is
  minimized to the decision, next steps, override, and optional note.
- [x] Local fallback is explicitly labelled process-local and cannot activate
  inside a Databricks deployment.
- [x] Active retrieval revalidates extracted evidence against preserved raw
  source fields and emits row/column receipts; fabricated spans fail closed.
- [x] Searchable rows preserve coordinates and validated operator type; known
  golden-path origins receive an explicitly straight-line distance.

## Required

- [ ] Workspace is Databricks Free Edition, not a paid/enterprise workspace.
- [ ] Organizer Marketplace dataset is accessible in that workspace.
- [ ] Profile output confirms `10,000` source records.
- [ ] Actual schema mapping and aggregate coverage are recorded: __________
- [ ] Evidence pipeline completed; broken literal receipts = `0`.
- [ ] Weak/incomplete record review completed by: __________
- [ ] Vector Search index attached and live retrieval revalidates literal spans.
- [ ] Lakebase Autoscaling resource attached.
- [ ] `identity-pepper` secret resource attached and readable by the App.
- [ ] Save -> fresh browser/new session -> reopen test passes.
- [ ] Databricks OAuth/CAN USE access and owner isolation pass every check in
  `docs/security/login-and-persistence-audit.md`.
- [ ] Facility results are challenge-data results, not silently seeded demo cards.
- [ ] Demo and persisted Lakebase rows contain no real patient/health data.
- [ ] Each shortlisted facility shows distance, evidence, gaps, and save action.
- [ ] Unknown/no-record state does not claim a facility or service is absent.
- [ ] App is deployed and loads reliably in a fresh browser.
- [ ] Git repository contains the exact deployed commit.
- [ ] One-minute demo has been rehearsed and timed.

## Record the proof

| Item | Value |
|---|---|
| Databricks App URL | |
| Deployed Git SHA | |
| Free Edition workspace verified by | |
| Dataset row count / verification time | |
| Evidence rows / broken receipt count | |
| Lakebase cross-session plan ID | |
| Vector Search index resource key | |
| Final smoke-test time | |
| Demo owner | |

## One-minute demo beats

1. **User/problem:** a patient coordinator or nontechnical planner needs a
   defensible referral, not another chatbot answer.
2. **Workflow:** enter location and care need; confirm the structured request.
3. **Decision:** compare up to three facilities with distance, literal evidence,
   ordinal trust, and missing facts.
4. **Human action:** save one option and a note; reopen it from a new session.
5. **Technical proof:** show Databricks evidence tables/Vector Search receipt and
   Lakebase persistence.
6. **Tradeoff:** `not documented` is intentionally not treated as `unavailable`;
   current price, capacity, and appointments remain unknown unless supported.

Full matrix: [`data-legend-official-brief-audit.md`](data-legend-official-brief-audit.md).
