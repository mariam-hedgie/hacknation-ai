-- Run this in the Lakebase SQL editor attached to the Databricks App.
-- It stores user-created state only, never facility claims or raw patient data.

CREATE TABLE IF NOT EXISTS saved_care_plans (
  plan_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS access_feedback (
  feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  plan_id TEXT NOT NULL,
  feedback_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS access_feedback_plan_id_idx
  ON access_feedback (plan_id, created_at, feedback_id);

-- Deployment gate: the App service principal must be able to insert, reopen,
-- update, and list these rows after a browser refresh and a new app session.
