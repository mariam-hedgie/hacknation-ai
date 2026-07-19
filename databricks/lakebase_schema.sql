-- Run in the Lakebase SQL editor attached to the Databricks App.
-- This schema stores pseudonymous user decisions only, never raw health intake.
-- If legacy tables without owner_id already exist, STOP and migrate or recreate
-- them before deploying. Do not point the app at the legacy plan_id-only schema.

DO $$
BEGIN
  IF to_regclass('saved_care_plans') IS NOT NULL
     AND NOT EXISTS (
       SELECT 1
       FROM information_schema.columns
       WHERE table_schema = current_schema()
         AND table_name = 'saved_care_plans'
         AND column_name = 'owner_id'
     ) THEN
    RAISE EXCEPTION
      'Unsafe legacy saved_care_plans schema: owner_id is missing. Migrate or recreate it.';
  END IF;
  IF to_regclass('access_feedback') IS NOT NULL
     AND NOT EXISTS (
       SELECT 1
       FROM information_schema.columns
       WHERE table_schema = current_schema()
         AND table_name = 'access_feedback'
         AND column_name = 'owner_id'
     ) THEN
    RAISE EXCEPTION
      'Unsafe legacy access_feedback schema: owner_id is missing. Migrate or recreate it.';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS saved_care_plans (
  owner_id TEXT NOT NULL
    CHECK (owner_id ~ '^[A-Za-z0-9_-]{1,128}$'),
  plan_id TEXT NOT NULL
    CHECK (plan_id ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$'),
  payload JSONB NOT NULL
    CHECK (jsonb_typeof(payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMPTZ NOT NULL
    DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
  PRIMARY KEY (owner_id, plan_id)
);

CREATE TABLE IF NOT EXISTS access_feedback (
  feedback_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  feedback_payload JSONB NOT NULL
    CHECK (jsonb_typeof(feedback_payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT access_feedback_owned_plan_fk
    FOREIGN KEY (owner_id, plan_id)
    REFERENCES saved_care_plans (owner_id, plan_id)
    ON DELETE CASCADE,
  CHECK (
    feedback_payload ->> 'status' IN (
      'helpful', 'needs_correction', 'not_sure', 'service_unavailable',
      'price_differed', 'accepted', 'not_visited'
    )
  ),
  CHECK (length(COALESCE(feedback_payload ->> 'note', '')) <= 500)
);

CREATE INDEX IF NOT EXISTS saved_care_plans_owner_updated_idx
  ON saved_care_plans (owner_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS access_feedback_owned_plan_idx
  ON access_feedback (owner_id, plan_id, created_at, feedback_id);

-- Deployment gates:
-- 1. Every app query binds owner_id from resolve_identity(), never UI input.
-- 2. Save/read/list/delete isolation is tested using two different owners.
-- 3. A scheduled job or safe startup task calls purge_expired().
-- 4. The App service principal gets database access; app users get CAN USE only.
