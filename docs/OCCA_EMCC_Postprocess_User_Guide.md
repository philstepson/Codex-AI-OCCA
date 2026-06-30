# OCCA EMCC Post-Processing User Guide

This guide describes the repeatable workflow for processing EMCC sizing extracts with the OCCA desktop Python package.

Treat all extracts and outputs as customer-sensitive. Do not edit raw extract files.

## Scope

This guide covers EMCC extracts shaped like:

```text
<work_dir>/
  emcc_sizing_extracts/
    *.csv
    *.txt
```

It does not cover AWR Miner post-processing, although the same audit principles apply.

## Required Inputs

- A customer working directory containing `emcc_sizing_extracts/`.
- The OCCA Python package installed in a Python 3.12+ environment.
- Customer cohort guidance if available.
- Customer approval for substitutions, exclusions, and provisional cohorting.

## Prerequisites and Version Freshness

Before processing customer data, activate the Python environment that contains OCCA and confirm it is Python 3.12 or newer:

```bash
python --version
```

Then run the local environment check:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/check_occa_environment.py
```

This reports the active Python executable, Python version, `occa` executable, and `occa --version` output.

The OCCA desktop wheel changes periodically. Before starting a sizing run, compare the installed version from:

```bash
occa --version
```

with the latest wheel on the OCCA releases page:

```text
https://occa.us.oracle.com/ords/r/occa/occa/occa-releases
```

The release page requires Oracle authentication and MFA, so this guide does not assume the version check can be fully automated. If a newer wheel is available, install it in the active Python environment, rerun the environment check, and review this skill's scripts against the new OCCA CLI output and generated artifact names before processing customer data.

## Standard Workflow

Run all OCCA commands from the customer working directory.

### 1. Inspect Extract Health

Use the skill script:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/inspect_emcc_extract.py <work_dir>
```

Review:

- file inventory
- CSV row counts
- error-like text matches
- current availability by target type
- metric timestamp ranges

Actual extract errors such as `ORA-` or `SP2-` need review before continuing. Job names containing words like `FAILED` are not automatically extract failures.

### 2. Run Pre-Flight

```bash
occa --pre-flight
```

Review:

- `occa_sizing_output/sizing/current_status_by_target_type.csv`
- `occa_sizing_output/sizing/current_status_by_target.csv`
- `occa_sizing_output/sizing/status_days_by_target.csv`

Pre-flight does not prove the extract is perfect. It tells whether OCCA can read the availability data and whether targets were healthy at collection time.

Typical review questions:

- Are many databases down, blacked out, or pending?
- Are hosts or agents down?
- Are important target types missing?
- Are current target counts plausible?

### 3. Generate Editable Property Files

```bash
occa --create-properties
```

Then create editable copies if they do not already exist:

```bash
cp occa_sizing_properties/properties_database_original.csv occa_sizing_properties/properties_database.csv
cp occa_sizing_properties/properties_instance_original.csv occa_sizing_properties/properties_instance.csv
cp occa_sizing_properties/properties_server_original.csv occa_sizing_properties/properties_server.csv
```

Do not edit the `_original.csv` files.

### 4. Assign Cohorts

The preferred path is customer-supplied cohort assignment.

Ask the customer to assign databases to meaningful cohorts such as:

- `Prod`
- `Non-Prod`
- `DR`
- application names
- site/lifecycle combinations

If customer cohorts are not available, use provisional cluster-based cohorts only with approval:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/assign_cluster_cohorts.py <work_dir>
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/assign_cluster_cohorts.py <work_dir> --apply
```

The dry run reports populated cluster counts and proposed cohort counts. The `--apply` mode backs up `properties_database.csv` and assigns:

```text
Cohort = cluster
```

Do not infer `Prod`, `Non-Prod`, or `DR` from names unless the customer provides a naming rule.

### 5. Apply Data Guard Defaults

```bash
occa --copy-db-name
```

Review `properties_database.csv` for:

- `Use Values from Database Name`
- `Use Values Scope`
- `Use Values Pct`

Physical standby mappings are common. Verify them against `emcc_sizing_structure_db_dr.csv`.

### 6. Apply Properties and Run Metric Analysis

```bash
occa --add-properties
occa --run-metric-analysis
```

If metric analysis completes, proceed to final verification. If it reports missing metrics, continue with the remediation workflow.

## Missing Metric Remediation

OCCA marks missing required property fields with `-1`. Required values commonly include:

- database allocated storage
- database used storage
- instance vCPU
- SGA
- PGA
- IOPS
- logons

Find candidates:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/find_missing_metric_candidates.py <work_dir>
```

### Acceptable Substitution Patterns

#### Data Guard Primary Copy

Use when a physical standby lacks usable metrics and the primary is present in the extract.

In `properties_database.csv`:

```text
Use Values from Database Name = <primary database name>
Use Values Scope = Physical Standby
```

Leave `Use Values Pct` blank unless the customer approves a specific override.

#### RAC Sibling Instance Copy

Use when one instance of a clustered database is missing all required instance metrics and a sibling instance for the same database is healthy.

In `properties_instance.csv`:

```text
Use Values from Instance = <healthy sibling instance>
```

This requires a reasonableness check. The sibling must be same database, same cluster, and comparable host class. The missing target should have evidence explaining why metrics are absent, such as blackout, target down, agent down, pending/unknown, or stale load time.

#### Explicit Exclusion

Use when no defensible substitute exists or the customer says the database should not be sized.

Record why the exclusion was made.

### Required Safeguards

Before changing property files:

- Create a timestamped backup.
- Identify the affected database or instance.
- Identify the missing fields.
- Identify the proposed source.
- Record the reason metrics are missing.
- Get user/customer approval for substitutions or exclusions.

After changing property files:

```bash
occa --add-properties
occa --run-metric-analysis
```

Repeat until OCCA completes or a decision is needed.

## Reasonableness Tests

Every substitution should pass these checks:

- The replacement comes from the same database, a known primary, or an approved alternate source.
- The affected target's availability history explains the gap.
- The replacement does not change instance/database counts unexpectedly.
- `metric_presence_by_stage.csv` shows the affected row becomes valid after the relevant replacement stage.
- `databases.csv` and `instances.csv` show no unintended exclusions.
- Cohort rollups remain plausible.
- Plots do not show obvious discontinuities or impossible values.

Use the verifier:

```bash
python /Users/PWSTEPHE/codex/AI-OCCA/skills/occa-emcc-postprocess/scripts/verify_occa_outputs.py <work_dir>
```

Clean-run expectations:

```text
properties_database.csv: negative_rows=0
properties_instance.csv: negative_rows=0
databases.csv: negative_rows=0, excluded_rows=0 unless approved
instances.csv: negative_rows=0, excluded_rows=0 unless approved
cohort_rollups.csv exists
sizing.csv exists
html_plots > 0
```

## Final Outputs

Primary review files:

```text
occa_sizing_output/sizing/databases.csv
occa_sizing_output/sizing/instances.csv
occa_sizing_output/sizing/servers.csv
occa_sizing_output/sizing/cohort_rollups.csv
occa_sizing_output/sizing/database_rollups.csv
occa_sizing_output/sizing/sizing.csv
occa_sizing_output/sizing/metric_presence_by_stage.csv
occa_sizing_output/plots/**/*.html
```

After outputs are clean enough:

```bash
occa --emcc-import
```

This creates:

```text
occa_sizing_output/occa_upload_data.json
```

## Audit Trail

For each run, keep notes covering:

- working directory
- OCCA version
- Python version
- pre-flight summary
- cohort method
- property file backups
- Data Guard copy directives applied
- missing metrics found
- substitutions or exclusions made
- approval status
- final verification output
- generated import JSON path, if created

## Calvert Pattern Captured

The Calvert run demonstrated the intended fallback pattern:

- Cohorts were assigned from cluster names because customer cohort names were unavailable.
- Two blackout/down RAC instance rows copied from healthy sibling instances.
- One physical standby used its primary database through `Physical Standby` scope.
- Raw extracts were preserved.
- Final metric analysis completed with no negative markers or unintended exclusions.
