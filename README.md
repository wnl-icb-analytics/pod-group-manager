# POD Group Manager

Streamlit-in-Snowflake app for assigning and maintaining POD group overview
mappings used by WNL urgent care / contracting reporting.

It replaces a manual monthly process (run a detection query → paste into Excel →
pick a POD group from a dropdown → `INSERT` into the lookup table) with an
interactive tool that detects unmapped combinations, lets you assign them, and
keeps a full audit trail.

## How it works

POD activity from trust LSACM data is grouped by three fields —
`POINT_OF_DELIVERY_CODE`, `LOCAL_POINT_OF_DELIVERY_CODE`,
`LOCAL_POINT_OF_DELIVERY_DESCRIPTION`. Each combination is assigned one of 18
`POD_GROUP_OVERVIEW_MASTER` values. The app owns these mappings in a dedicated
schema and exposes a backward-compatible view for downstream reporting.

### Source of truth

`DATA_LAKE__NCL.POD_GROUP_MANAGER` is the master. The legacy table
`DATA_LAKE__NCL.ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW` is **never
written to** — it is seeded once (read-only) and downstream reporting repoints to
`V_POD_GROUP_OVERVIEW`, which reproduces the legacy shape (including the
`POD_LOOKUP` key and `'?'`-filled component columns) exactly.

## Schema

| Object | Purpose |
|---|---|
| `POD_GROUP_MAPPING` | Master mappings. Component fields stored with real NULLs; `POD_LOOKUP` kept for join parity |
| `POD_GROUP_OPTION` | The 18 dropdown values — governed, sortable, activatable |
| `POD_GROUP_PROVIDER` | In-scope provider codes for unmapped detection |
| `POD_GROUP_MAPPING_CHANGES` | Audit history (who/when/old→new/why) |
| `V_POD_GROUP_OVERVIEW` | Backward-compatible view for downstream |
| `V_UNMAPPED_PODS` | Unmapped combinations in the latest file per provider, with volume |

Writes go through stored procedures (`UPSERT_POD_MAPPING`,
`UPDATE_POD_MAPPING_GROUP`, `DELETE_POD_MAPPING`, `UPSERT_POD_OPTION`) which
generate the key, validate the chosen group and log the change.

## Pages

- **Unmapped** — pick a financial year, see unmapped combinations ranked by
  volume, assign a group (+ note) per row in a grid, save in bulk.
- **Mappings** — search/filter existing mappings, change a group
  retrospectively, delete, view per-mapping history.
- **Analytics** — totals, mappings per POD group, recent activity.
- **Options** — manage the dropdown values.

## Deploy

Run the SQL in order, then create the app:

```sql
-- 1-4: schema, seed, views, procedures (role ENGINEER)
@sql/01_schema.sql
@sql/02_seed_from_existing.sql
@sql/03_views.sql
@sql/04_procedures.sql
-- 5: Git integration + Streamlit object
@sql/05_git_integration.sql
```

Update the app after pushing changes:

```sql
ALTER GIT REPOSITORY EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO FETCH;
```

The signed-in Streamlit user's email is recorded as the actor on every change.
