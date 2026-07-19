# AI Search setup gate

The original brief requires Mosaic AI Vector Search (now Databricks AI Search)
for retrieval across the 10,000 facility rows. The active app queries the
corrected Model B table built by `extract_data.py` and `flatten_data.py`.

## Required source-table contract

Table: `workspace.default.facilities_searchable`

Required index fields:

- `unique_id` — stable primary key and row receipt;
- `search_text` — embedding source assembled from facility name and extracted
  claim groups;
- `raw_description`, `raw_capability`, `raw_procedure`, `raw_equipment` —
  original source fields used for literal receipt revalidation;
- `latitude`, `longitude`, `address_city`, `facility_type`, `operator_type` —
  distance and preference inputs;
- extracted specialties/capabilities/procedures/equipment/facts and
  `data_quality` — candidate interpretation, never ground truth by itself.

Before creating the index, confirm the table has Change Data Feed enabled:

```sql
ALTER TABLE workspace.default.facilities_searchable
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

## Create the endpoint and index

In the Databricks Free Edition UI:

1. Create an AI Search endpoint named exactly `aven-facility-search`.
2. Create a Delta Sync index over
   `workspace.default.facilities_searchable`.
3. Use `unique_id` as the primary key.
4. Use `search_text` as the embedding source.
5. Use Triggered sync for a predictable demo.
6. Retain all fields listed in the source-table contract above.
7. Sync and wait until the index reports online.
8. Add the index to the Databricks App with **Can select** and the exact custom
   resource key `facility-evidence-index`.

The committed `app.yaml` maps that resource into
`AVEN_VECTOR_SEARCH_INDEX` and uses the fixed endpoint name above.

## Trust rule

Semantic similarity is candidate discovery, not evidence. Before a claim can be
shown as documented, `src/backend/agent_bricks.py`:

1. selects the extracted entry matching the requested capability;
2. finds its evidence span in the preserved original raw field;
3. emits the raw field and `unique_id` as the receipt;
4. fails closed to `not_documented` when no literal receipt exists;
5. retains conflicts and missing fields as visible uncertainty.

## Final proof

- [ ] Index is online and returns row ID, raw receipt fields, coordinates, and
  extracted claim fields.
- [ ] A nonsense/absent capability does not become documented merely because a
  similar row was returned.
- [ ] A deliberately mismatched extracted span becomes `not_documented`.
- [ ] App service identity can query the index without a personal token.
- [ ] Retrieval remains live after a fresh App deployment.

Official current references:

- [Create AI Search endpoints and indexes](https://docs.databricks.com/aws/en/ai-search/create-ai-search)
- [Add an AI Search index to a Databricks App](https://docs.databricks.com/gcp/en/dev-tools/databricks-apps/vector-search)
