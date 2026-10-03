# OCCA EMCC Workflow Reference

## Directory Contract

Expected input:

```text
<work_dir>/
  emcc_sizing_extracts/
    *.csv
    *.txt  # may be absent after customer-side filtering/obfuscation
```

Generated directories:

```text
<work_dir>/
  occa_sizing_properties/
  occa_sizing_output/
```

Do not modify `emcc_sizing_extracts/`.

For new customer collection, use the supplied `Customer_emcc_sizing_extracts-26.9.1.zip` and its bundled `Readme-EMCC-Extract.txt` / `Extracts-Users-Guide.pdf`. This release names the Unix launcher `Get_EMCC_Sizing_Interactive` and the Windows file `Get_EMCC_Sizing_Interactive_ps1` (rename to `.ps1` for PowerShell). The repository OCCA sizing guide still shows older `.sh` / `.ps1` launcher names. Confirm `extracts/version.txt` reports 26.9.1. The extract bundle also includes `awr_pdb_miner.sql`; the standalone `AWR-Miner-26.9.1.zip` has the same collection family for AWR-only work.

## Environment Freshness

Before processing customer data, confirm the active Python and OCCA CLI:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/check_occa_environment.py
```

The 26.9.1 wheel requires Python 3.9 or newer; this repository selects `pws-venv.3.12.8`. The OCCA desktop wheel changes from time to time, so compare the installed version from `occa --version` with the latest wheel on the OCCA releases page:

```text
https://occa.us.oracle.com/ords/r/occa/occa/occa-releases
```

The release page requires Oracle authentication and MFA. The local checker can report the installed version and the release URL, but it cannot prove that the wheel is current without an authenticated user check.

The supplied 26.9.1 wheel and extract bundles are a matched local release. Compare versions before a customer run; if a newer wheel is installed, recheck the skill scripts and generated artifact names. The supplied `OCCA_User_Guide.pdf` is byte-identical to the repository copy, so it does not describe every 26.9.1 code change.

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
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/generate_occa_summary_report.py .
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

Summary report:

- `Sizing.html`

Import:

- `occa_sizing_output/occa_upload_data.json`

## Clean-Run Criteria

Before import, verify:

- No included property row has unresolved required override fields set to `-1`. In 26.9.1, those markers mean required telemetry was absent after replacements; a collected zero remains valid.
- `databases.csv` and `instances.csv` have no unintended exclusions; review their `excluded_reason` values.
- `cohort_rollups.csv` exists and contains real cohorts, not only `excluded` or `unassigned`.
- Any substitution is documented with source evidence and user/customer approval. Review `metric_presence_by_stage.csv` at the final replacement stage when diagnosing absence.
- Plots were generated and reviewed for obvious discontinuities or unexpected cohort shapes.
- If generated, `Sizing.html` opens from the work directory and links to the real OCCA sizing CSVs and plot HTML files.
