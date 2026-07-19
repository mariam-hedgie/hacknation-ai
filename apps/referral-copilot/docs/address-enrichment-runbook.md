# Facility address enrichment runbook

The source facility snapshot remains immutable. Address discovery writes to the
separate `data/facility_address_candidates.jsonl` ledger, keyed by stable
`facility_id`. This ledger is ignored by Git because it is a generated data
artifact, not product source code.

Each row preserves the facility name, source URL, source excerpt, retrieval
time, optional address/coordinates, and a review status. Tavily results are
always `candidate` records. They are not evidence of a branch address, service,
or distance.

## Safe workflow

1. Set a Tavily budget and rate limit before running a batch. Start with 25.
2. Run a dry run:

   ```bash
   cd apps/referral-copilot
   ../../.venv/bin/python scripts/enrich_facility_addresses.py \
     --input data/facilities_searchable.jsonl --max-records 25
   ```

3. With a configured server-side `TAVILY_API_KEY`, run `--apply`.
4. Review every candidate against an official facility, government, regulator,
   or attributable directory page. Resolve branch ambiguity before adding an
   address. Record the exact address and coordinates only after verification;
   set `review_status` to `verified`, `reviewer`, and `reviewed_at`.
5. Geocode a verified street address through the selected map provider. Keep
   that provider, retrieval time, and attribution in the production table.
6. Import only verified records into `facility_branch_locations` (production)
   or the local verified ledger. Candidate rows must never drive a route or a
   kilometre filter.

## Production table contract

Use a migration to create `facility_branch_locations` separately from the
facility-evidence table. Key it by `facility_id` plus a branch identifier.
Required fields: source URL, source retrieval time, review state, reviewer,
address text, latitude/longitude, and an update timestamp. Add address data as
nullable first, backfill in batches, and create indexes concurrently. Do not
alter challenge evidence rows or overwrite a prior source without retaining an
audit record.
