# AI Search (Vector Search) setup gate

> **Superseded input table** (see TODO.md "Decision — Model B adopted"): the
> steps below were written against Model A's `facility_source_chunks`, which
> was never built. The real table to index is
> `workspace.default.facilities_searchable` (one row per facility; see
> `../flatten_data.py`), keyed by `unique_id` rather than `chunk_id`, with the
> embedding source drawn from `capabilities`/`procedures`/`equipment`/
> `facility_facts`/`specialties` instead of a single `literal_source_text`
> column. The gate checklist and the "semantic similarity is not evidence"
> guidance below still apply; only the source table/columns must be swapped.
> `src/backend/vector_search.py::retrieve()` already queries
> `facilities_searchable` with the real column names.

The original brief lists Mosaic AI Vector Search and the technical rubric asks
whether it is used well. Configure it only after
`02_build_evidence_tables.py` has created
`<target_schema>.facility_source_chunks` with:

- `chunk_id` — primary key;
- `source_row_id` — row receipt;
- `source_column` — field receipt;
- `literal_source_text` — the unmodified source chunk.

In the Databricks Free Edition UI:

1. Open Catalog Explorer and select `facility_source_chunks`.
2. Choose **Create -> Vector search index**.
3. Use a **Delta Sync** index, `chunk_id` as the primary key,
   `literal_source_text` as the embedding source, and **Triggered** sync for a
   predictable hackathon demo.
4. Retain `source_row_id`, `source_column`, and `literal_source_text` in the
   synced columns.
5. Sync the index, then add it to the Databricks App as an **AI Search index**
   resource with `Can select` only.
6. Give the resource a stable key, for example `facility_evidence_index`, and
   expose its full index name through `app.yaml` using `valueFrom` only after the
   workspace owner confirms that key.

Use the index to find candidate source chunks. Semantic similarity is **not**
evidence by itself. Before a result becomes a facility claim, Aven must still:

1. resolve the chunk to its source row and field;
2. extract or select the candidate literal span;
3. verify the span occurs in `literal_source_text`;
4. evaluate corroboration/conflicts;
5. show the receipt and uncertainty in the UI.

Final proof:

- [ ] Index is online and a query returns the row ID, column, and literal text.
- [ ] A nonsense/absent capability does not become a documented claim merely
  because a semantically similar chunk was returned.
- [ ] App service identity can select the index without a personal token.
- [ ] Retrieval remains usable after a fresh App deployment.

Official current setup reference:
[Create AI Search endpoints and indexes](https://docs.databricks.com/aws/en/vector-search/create-vector-search).
