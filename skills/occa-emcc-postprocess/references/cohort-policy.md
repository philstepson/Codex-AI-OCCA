# Cohort Policy

## Default Preference

Ask whether the customer supplied cohort assignments. This is the normal and preferred case. Customer cohorts often reflect application, lifecycle, security, operational isolation, maintenance windows, and blast-radius decisions that are not visible in EMCC telemetry.

Common customer labels include:

- `Prod`
- `Non-Prod`
- `DR`
- application names
- site/lifecycle combinations

## Provisional Cohorts

When customer cohort data is unavailable, use a provisional cohort model only after explaining the limitation.

Preferred fallback:

```text
Cohort = cluster
```

Reasoning:

- RAC databases can span multiple servers.
- Cluster is usually closer to the operational workload boundary than individual host.
- Cluster aligns better with shared failure domain, patching, placement, and administration.

Fallback when cluster is blank or unusable:

```text
Cohort = server list or primary server
```

Do not infer `Prod`, `Non-Prod`, or `DR` from names unless the customer gives a naming convention.

## Safeguards

Before applying cluster cohorts:

- Confirm `properties_database.csv` exists.
- Count populated and blank `cluster` values.
- If any cluster is blank, report the affected count and do not proceed automatically.
- Create a timestamped backup of `properties_database.csv`.
- Populate only the `Cohort` column.
- Report cohort counts.

After applying:

- Run `occa --add-properties`.
- Confirm `Cohort` was replaced for all database rows.
- Review `cohort_rollups.csv` after metric analysis.

## Customer Review

Present provisional cohorts as a mapping table for customer validation:

```text
cluster -> provisional cohort -> database count -> instance count -> notes
```

Ask the customer to rename or merge cohorts before final sizing when possible.
