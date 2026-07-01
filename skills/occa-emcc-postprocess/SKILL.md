---
name: occa-emcc-postprocess
description: Use when processing Oracle Cloud Capacity Analytics EMCC sizing extracts with the OCCA CLI, including pre-flight health review, property generation, cohort assignment, Data Guard copy directives, missing-metric remediation, metric analysis, and final artifact verification.
---

# OCCA EMCC Postprocess

Use this skill for Oracle Cloud Capacity Analytics EMCC extract post-processing. Treat all extract and output data as customer-sensitive.

## Guardrails

- Do not edit files under `emcc_sizing_extracts/`; preserve raw extracts as evidence.
- Make corrections only in generated property files under `occa_sizing_properties/`.
- Back up every property file before changing it.
- Prefer customer-supplied cohort assignments. If unavailable and the user approves, assign provisional cohorts from `cluster`; use server only when cluster is missing or not meaningful.
- Do not invent missing values. Use defensible copy directives, alternate extract evidence, or explicit exclusion with a reason.
- Summaries should avoid exposing customer identifiers unless the user asks for details.

## Workflow

1. Confirm the local OCCA environment is suitable:
   - Run `scripts/check_occa_environment.py`.
   - Use Python 3.12 or newer for the active environment.
   - Compare `occa --version` with the latest wheel listed on the OCCA releases page before processing customer data.
   - The release page requires Oracle authentication/MFA, so do not treat a failed automated web check as proof that the local wheel is current.
2. Confirm the working directory contains `emcc_sizing_extracts/*.csv` and `*.txt`.
3. Inspect extract health:
   - Run `scripts/inspect_emcc_extract.py <work_dir>`.
   - Check for `ORA-`, `SP2-`, traceback, and extract errors.
4. Run pre-flight:
   - `occa --pre-flight`
   - Review `occa_sizing_output/sizing/current_status_by_target_type.csv`.
5. Generate properties:
   - `occa --create-properties`
   - Copy `*_original.csv` to editable property names if missing.
6. Assign cohorts:
   - Ask for customer-provided cohorts first.
   - If unavailable and approved, run `scripts/assign_cluster_cohorts.py <work_dir> --apply`.
7. Apply Data Guard defaults:
   - `occa --copy-db-name`
   - Review populated `Use Values from Database Name` and `Use Values Scope`.
8. Apply properties and run analysis:
   - `occa --add-properties`
   - `occa --run-metric-analysis`
9. If OCCA reports missing metrics:
   - Run `scripts/find_missing_metric_candidates.py <work_dir>`.
   - Read `references/missing-metrics.md`.
   - Apply only approved property edits, then rerun `--add-properties` and `--run-metric-analysis`.
10. Verify final artifacts:
   - Run `scripts/verify_occa_outputs.py <work_dir>`.
   - Confirm no unintended `-1` markers, exclusions, or missing key artifacts.
11. Generate a current-state summary report when a dashboard-style review artifact is useful:
   - Run `scripts/generate_occa_summary_report.py <work_dir>`.
   - Confirm the generated `Sizing.html` links to the real files under `occa_sizing_output`.
12. Create import JSON only after the run is clean enough for review:
   - `occa --emcc-import`

## References

- Read `references/workflow.md` for command sequence and expected artifacts.
- Read `references/cohort-policy.md` before assigning provisional cohorts.
- Read `references/missing-metrics.md` before making substitution or exclusion decisions.
