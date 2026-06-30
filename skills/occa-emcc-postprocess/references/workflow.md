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

## Environment Freshness

Before processing customer data, confirm the active Python and OCCA CLI:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/check_occa_environment.py
```

The active Python environment should be Python 3.12 or newer. The OCCA desktop wheel changes from time to time, so compare the installed version from `occa --version` with the latest wheel on the OCCA releases page:

```text
https://occa.us.oracle.com/ords/r/occa/occa/occa-releases
```

The release page requires Oracle authentication and MFA. The local checker can report the installed version and the release URL, but it cannot prove that the wheel is current without an authenticated user check.

If a newer wheel is installed, rerun this skill's environment check and review the skill scripts against the new OCCA command output and generated artifact names before using automation for customer data.

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
