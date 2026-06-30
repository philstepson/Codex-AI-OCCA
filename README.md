# AI-OCCA

AI-OCCA is a working repository for Oracle Cloud Capacity Analytics sizing automation.

OCCA uses historical Oracle database workload data to support comparative sizing for future-state Oracle Cloud platforms. The main inputs are EMCC repository extracts and OCCA AWR Miner outputs. The main local processing tool is the OCCA Python package distributed as:

```text
occa-26.3.0-py3-none-any.whl
```

## Repository Contents

```text
Customer_emcc_sizing_extracts-26.2.0.zip  Customer-side EMCC/AWR collection scripts
OCCA_User_Guide.pdf                       OCCA sizing workflow and command reference
occa-26.3.0-py3-none-any.whl             OCCA desktop analytics package
AGENTS.md                                Codex operating instructions
.codex/OCCA_CONTEXT.md                   Extracted project context
.codex/OCCA_AUTOMATION_PLAN.md           Initial automation plan and open questions
docs/OCCA_EMCC_Postprocess_User_Guide.md Repeatable EMCC post-processing guide
skills/occa-emcc-postprocess/            Codex skill for EMCC post-processing
```

## High-Level Workflow

1. Customer runs the EMCC collection scripts or OCCA AWR Miner scripts.
2. Customer returns a zip containing `emcc_sizing_extracts` or `awr_miner_out` data.
3. Oracle runs the OCCA desktop analytics package in a customer-specific working directory.
4. Generated property files are reviewed and edited for cohorts, exclusions, missing metrics, and Data Guard directives.
5. OCCA metric analysis creates sizing CSVs, plots, and upload JSON.
6. Upload JSON is reviewed in OCCA Web for target selection and sizing report production.

## First Local Setup

Create a virtual environment in each processing workspace or in a shared local tool directory, then install the wheel:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install /Users/PWSTEPHE/codex/AI-OCCA/occa-26.3.0-py3-none-any.whl
.venv/bin/occa --help
```

Customer extract data should live in separate customer working directories, not directly in this repository unless the user requests that layout.

## Repeatable EMCC Post-Processing

This repository includes a Codex skill and user guide for repeatable EMCC sizing extract post-processing:

- [OCCA EMCC Post-Processing User Guide](docs/OCCA_EMCC_Postprocess_User_Guide.md)
- [OCCA EMCC Codex Skill](skills/occa-emcc-postprocess/SKILL.md)

The workflow is customer-cohort-first. When customer cohort assignments are unavailable, the documented fallback is to assign provisional cohorts from cluster names, then have the customer map those cluster cohorts to real environment names later.

The skill also includes helper scripts for repeatable validation:

```text
skills/occa-emcc-postprocess/scripts/inspect_emcc_extract.py
skills/occa-emcc-postprocess/scripts/assign_cluster_cohorts.py
skills/occa-emcc-postprocess/scripts/find_missing_metric_candidates.py
skills/occa-emcc-postprocess/scripts/verify_occa_outputs.py
```

Missing metric substitutions must be backed by evidence, reasonableness checks, and user/customer approval. Raw extract files should not be edited.
