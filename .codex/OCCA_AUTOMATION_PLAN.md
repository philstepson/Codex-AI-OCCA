# OCCA Automation Plan

## Goal

Create a reliable, evidence-preserving workflow that lets Codex help process customer EMCC/AWR extract zips with the existing OCCA package, identify issues, guide required property edits, and produce sizing artifacts for review and upload.

## Phase 1 - Baseline Project Setup

- Keep `OCCA_User_Guide.pdf`, `Customer_emcc_sizing_extracts-26.2.0.zip`, and `occa-26.3.0-py3-none-any.whl` as local source artifacts.
- Use `AGENTS.md` as the canonical Codex instruction file.
- Use separate customer working directories for actual extract processing.
- Before processing, install `occa-26.3.0` into a virtual environment and capture `occa --help` and `occa --version`.

## Phase 2 - Intake Automation

Build a wrapper/checklist that accepts:

- Customer name or opportunity identifier.
- Path to customer zip.
- Extract type: EMCC or AWR, auto-detected where safe.
- Whether data is filtered or obfuscated.
- Expected EMCC repositories, sites, and customer notes.

The intake should:

- Create a customer working directory.
- Preserve the original zip.
- Extract into the expected folder shape.
- Validate presence of CSV/TXT files for EMCC or `.out` files for AWR.
- Search extracted files for `ORA-` and other obvious execution errors.
- Produce an intake summary markdown file.

## Phase 3 - EMCC Processing Automation

Automate command execution and evidence capture around:

```bash
occa --pre-flight
occa --create-properties
occa --copy-db-name
occa --add-properties
occa --run-metric-analysis
occa --emcc-import
```

The wrapper should stop for user/customer decisions after property generation and after each metric-analysis review when databases are excluded or missing fields.

Evidence to summarize:

- `occa_sizing_output/sizing/current_status_by_target_type.csv`
- `occa_sizing_output/sizing/current_status_by_target.csv`
- `occa_sizing_output/sizing/databases.csv`
- `occa_sizing_output/sizing/instances.csv`
- `occa_sizing_output/sizing/servers.csv`
- `occa_sizing_output/sizing/cohort_rollups.csv`
- log files under `occa_sizing_output/log`
- existence of `occa_sizing_output/occa_upload_data.json`

## Phase 4 - AWR Processing Automation

Automate command execution and evidence capture around:

```bash
occa --awr-parse
occa --awr-plot
occa --awr-run
occa --awr-import
```

The wrapper should stop after plot/property generation for timezone and cohort edits, then review snapshot overlap before import.

Evidence to summarize:

- `awr_miner_occa/properties/awr_tz_database.csv`
- `awr_miner_occa/properties/awr_properties_database.csv`
- `awr_miner_occa/sizing/databases.csv`
- `awr_miner_occa/sizing/instances.csv`
- snapshot coverage plot existence
- existence of `awr_miner_occa/awr_occa_upload_data.json`

## Phase 5 - Review Reports

Create small generated markdown reports for each run:

- Intake summary.
- Pre-flight target health summary.
- Missing metrics and implicit exclusions.
- Cohort assignment summary.
- Data Guard directive summary.
- Final artifact manifest.
- Open decisions for the user/customer.

## Open Questions For The User

1. Where should customer working directories live by default?
2. Should Codex create and manage the Python virtual environment in this repository, in each customer work directory, or in a shared tool path?
3. What customer/opportunity naming convention should be used for generated run folders?
4. What default cohort model should be assumed when the customer has not provided one?
5. Which target platforms should the first automation focus on: Exadata Database Service on Dedicated Infrastructure, Exadata Cloud@Customer, Base Database Service, Autonomous, or multiple?
6. Should source-side filtered or obfuscated extracts be treated differently in summaries?
7. What threshold should block progress automatically: any `ORA-`, any missing required extract file, any implicit exclusions, or only severe errors?
8. Should generated upload JSON ever be opened or inspected for sensitive fields, or only validated for existence/schema?

