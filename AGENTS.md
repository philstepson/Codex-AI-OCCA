# AI-OCCA Codex Instructions

This repository supports Oracle Cloud Capacity Analytics (OCCA) sizing work. Treat it as an Oracle-internal, customer-data-sensitive project for processing EMCC and OCCA AWR Miner extracts into OCCA sizing artifacts.

## Core Context

- OCCA implements comparative sizing for Oracle database workloads moving to Oracle Cloud platforms.
- The primary customer data path is EMCC extracts from the Enterprise Manager Cloud Control repository, usually containing inventory, database/host/PDB structure, properties, availability, and resource-consumption metrics.
- OCCA can also process OCCA AWR Miner `.out` files, but those generally have less history than EMCC extracts.
- The local package is `occa-26.3.0-py3-none-any.whl`; it exposes the console scripts `occa` and `occa_api`.
- The user guide is `OCCA_User_Guide.pdf`; it is the authoritative local workflow reference.
- The customer extract script bundle is `Customer_emcc_sizing_extracts-26.2.0.zip`.

## Data Handling

- Assume all customer extracts may contain confidential customer, database, host, owner, and workload information.
- Do not modify files in `emcc_sizing_extracts`, `emcc_sizing_extracts_filtered`, `emcc_sizing_extracts_obfuscated`, or `awr_miner_out` unless the user explicitly asks.
- Correct missing or invalid sizing inputs through generated property files, not by editing raw extracts.
- Preserve customer-provided zip files and raw extracted folders as evidence.
- Before sharing output summaries, avoid exposing sensitive identifiers unless the user asks for detail.

## Expected Working Directory Shapes

For EMCC extract processing, work inside a customer-specific directory that contains:

```text
<work_dir>/
  emcc_sizing_extracts/
    *.csv
    *.txt
```

For OCCA AWR Miner processing, work inside a customer-specific directory that contains:

```text
<work_dir>/
  awr_miner_out/
    *.out
```

Generated directories may include `occa_sizing_properties`, `occa_sizing_output`, `awr_miner_parsed`, `awr_miner_plots`, and `awr_miner_occa`.

## EMCC Workflow

Use the guide and current package help as the source of truth. The typical EMCC workflow is:

1. Unpack the customer-provided data into `emcc_sizing_extracts`.
2. Check for extract errors, especially `ORA-` messages in CSV/TXT files.
3. Run `occa --pre-flight` after extracts exist to summarize target health.
4. Run `occa --create-properties`.
5. Copy generated `*_original.csv` property files to editable names without `_original`.
6. Run `occa --copy-db-name` to set default Data Guard copy directives.
7. Edit properties with customer decisions, especially `Cohort`, exclusions, overrides, Data Guard directives, and missing-metric substitutions.
8. Run `occa --add-properties`.
9. Run `occa --run-metric-analysis`; use `--checkmetrics` when needed.
10. Review `occa_sizing_output/sizing/databases.csv`, `instances.csv`, `servers.csv`, and cohort rollups for exclusions, missing metrics, and sanity checks.
11. Iterate property edits, add-properties, and metric analysis until sizing outputs are clean enough.
12. Run `occa --emcc-import` to create `occa_sizing_output/occa_upload_data.json`.
13. Run `occa --reports` or `occa --create-artifacts` when useful.

## AWR Miner Workflow

The typical AWR workflow is:

1. Put customer `.out` files in `awr_miner_out`.
2. Run `occa --awr-parse`.
3. Run `occa --awr-plot`.
4. Copy generated AWR property originals to editable names.
5. Set each database timezone in `awr_tz_database.csv`.
6. Set cohorts in `awr_properties_database.csv`.
7. Run `occa --awr-run`.
8. Review `awr_miner_occa/sizing/databases.csv`, `instances.csv`, and snapshot overlap plots.
9. Run `occa --awr-import` to create `awr_miner_occa/awr_occa_upload_data.json`.

## Automation Priorities

- Prefer repeatable scripts/checklists around the existing `occa` CLI rather than reimplementing sizing formulas.
- Build wrappers that validate directory shape, extract completeness, ORA errors, generated property files, exclusions, and expected output artifacts.
- Keep an audit trail of commands run, generated files, and user/customer decisions.
- When something fails, preserve logs from `occa_sizing_output/log` or AWR output directories before retrying.
- Ask the user for customer-specific cohort rules, exclusion rules, Data Guard handling, target platform assumptions, and acceptable missing-metric substitutions.

## Local Setup Notes

- Use Python 3.9 or newer.
- Install the wheel into a project/customer virtual environment before running `occa`.
- Inspect `occa --help` and `occa --version` after installation because the package may change.
- The package may attempt version/logging network calls; network failures should not be treated as sizing failures unless the OCCA command itself fails.

