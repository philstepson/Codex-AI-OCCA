# OCCA EMCC Workflow Reference

## Directory Contract

Expected input:

```text
<work_dir>/
  emcc_sizing_extracts/
    *.csv
    *.txt
```

Generated directories:

```text
<work_dir>/
  occa_sizing_properties/
  occa_sizing_output/
```

Do not modify `emcc_sizing_extracts/`.

## Command Sequence

Use the installed OCCA CLI for sizing logic. Do not reimplement sizing formulas.

```bash
occa --pre-flight
occa --create-properties
cp occa_sizing_properties/properties_database_original.csv occa_sizing_properties/properties_database.csv
cp occa_sizing_properties/properties_instance_original.csv occa_sizing_properties/properties_instance.csv
cp occa_sizing_properties/properties_server_original.csv occa_sizing_properties/properties_server.csv
occa --copy-db-name
occa --add-properties
occa --run-metric-analysis
```

After a clean analysis:

```bash
occa --emcc-import
```

## Key Outputs

Pre-flight:

- `occa_sizing_output/sizing/current_status_by_target.csv`
- `occa_sizing_output/sizing/current_status_by_target_type.csv`
- `occa_sizing_output/sizing/status_days_by_target.csv`

Property files:

- `occa_sizing_properties/properties_database.csv`
- `occa_sizing_properties/properties_instance.csv`
- `occa_sizing_properties/properties_server.csv`

Metric analysis:

- `occa_sizing_output/sizing/databases.csv`
- `occa_sizing_output/sizing/instances.csv`
- `occa_sizing_output/sizing/servers.csv`
- `occa_sizing_output/sizing/metric_presence_by_stage.csv`
- `occa_sizing_output/sizing/sizing.csv`
- `occa_sizing_output/sizing/database_rollups.csv`
- `occa_sizing_output/sizing/cohort_rollups.csv`
- `occa_sizing_output/sizing/database_statistics.csv`
- `occa_sizing_output/sizing/cohort_statistics.csv`
- `occa_sizing_output/plots/**/*.html`

Import:

- `occa_sizing_output/occa_upload_data.json`

## Clean-Run Criteria

Before import, verify:

- No property row has required override fields still set to `-1`.
- `databases.csv` and `instances.csv` have no unintended exclusions.
- `cohort_rollups.csv` exists and contains real cohorts, not only `excluded` or `unassigned`.
- Any substitution is documented with source evidence and user/customer approval.
- Plots were generated and reviewed for obvious discontinuities or unexpected cohort shapes.
