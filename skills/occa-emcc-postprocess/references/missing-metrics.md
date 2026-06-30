# Missing Metrics Policy

OCCA marks missing required values in property files with `-1`. These must be resolved before a clean metric-analysis run.

## Resolution Order

Use this order:

1. Verify whether the target should be excluded.
2. Check availability and EM metric collection health.
3. Use Data Guard primary/standby copy directives when appropriate.
4. For RAC instance gaps, copy from a healthy sibling instance only when the sibling is same database, same cluster, similar host class, and the missing instance is down, blacked out, stale, or agent impaired.
5. Use alternate EMCC metric windows only when the metric exists for the same target and is temporally close enough to be defensible.
6. Use host-level data only as a sanity check, not as a direct substitute for database metrics unless explicitly approved.
7. Exclude with a clear reason when no defensible substitute exists.

## Common Evidence Sources

- `occa_sizing_properties/properties_database.csv`
- `occa_sizing_properties/properties_instance.csv`
- `emcc_sizing_extracts/emcc_sizing_structure_db.csv`
- `emcc_sizing_extracts/emcc_sizing_structure_db_dr.csv`
- `emcc_sizing_extracts/emcc_sizing_availability_history.csv`
- `emcc_sizing_extracts/emcc_sizing_em_metrics.csv`
- `emcc_sizing_extracts/emcc_sizing_metrics_db_hourly_03_months.csv`
- `emcc_sizing_extracts/emcc_sizing_metrics_db_daily_*.csv`
- `emcc_sizing_extracts/emcc_sizing_metrics_host_*.csv`

## Data Guard

If a physical standby has missing metrics and the primary is known, prefer:

```text
Use Values from Database Name = <primary database name>
Use Values Scope = Physical Standby
```

Leave `Use Values Pct` blank unless the customer approves a custom percentage. OCCA's default physical standby handling uses the configured `PHYSICAL_STANDBY_PCT`.

If the Data Guard extract has a primary unique name but blank primary target name/GUID, search `properties_database.csv` and structure files for the matching primary database target before deciding.

## RAC Sibling Instance Copy

This is acceptable when:

- The missing row is one instance of a clustered database.
- A sibling instance for the same database has valid metrics.
- The missing instance has availability evidence such as `Blackout`, `Target Down`, `Agent Down`, stale load time, or `Pending/Unknown`.
- The substitution is documented and approved.

Use:

```text
Use Values from Instance = <healthy sibling instance>
```

Clear stale `-1` values from required override columns after a higher-level copy directive handles the metric, but only after rerun evidence shows the output rows are no longer excluded.

## Reasonableness Checks

Before accepting substitutions:

- Re-run `occa --add-properties` and `occa --run-metric-analysis`.
- Verify no negative markers remain in property files.
- Verify `databases.csv` and `instances.csv` have no unintended exclusions.
- Review `metric_presence_by_stage.csv` for the affected rows after stage 2 or stage 3.
- Compare final cohort rollups against expected database and instance counts.
- Review generated plots for discontinuities or implausible changes.

## Approval Notes

Record for each substitution:

- affected database/instance
- missing fields
- reason missing
- replacement source
- evidence files used
- user/customer approval status
- date/time of edit
