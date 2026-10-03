---
name: occa-emcc-postprocess
description: Process Oracle Cloud Capacity Analytics EMCC extracts or OCCA AWR Miner output with the OCCA CLI, including extract validation, properties, cohorts, missing metrics, analysis, and import review.
---

# OCCA post processing

Use the installed `occa` CLI for sizing; do not reimplement its formulas. Treat extracts, properties, logs, and outputs as customer sensitive. The repository's `OCCA_User_Guide.pdf` is the workflow reference; inspect `occa --help` and `occa --version` for the installed release. The 26.9.1 wheel, AWR Miner bundle, and EMCC customer scripts supplied in `New-OCCA-9-2026` form a matched release. Check the actual versions before customer processing.

## Guardrails

- Preserve customer supplied archives and raw `emcc_sizing_extracts/` or `awr_miner_out/` files. Make sizing corrections in generated property files; back up each property file before editing.
- Obtain customer decisions for cohorts, exclusions, Data Guard treatment, target platform, and missing metric substitutions. If cohorts are unavailable, use the provisional cluster mapping only with user approval.
- Do not infer a missing metric from a numeric zero. In 26.9.1, OCCA checks whether required telemetry was collected after instance and database replacements. A collected zero can be valid; an unresolved missing value is marked `-1` in an editable property file.
- Review OCCA's excluded rows and reasons before import. A command's exit code and output files both matter; preserve logs when a run fails.
- Avoid exposing customer identifiers in summaries unless the user asks for detail.

## EMCC route

1. Confirm the active environment with `scripts/check_occa_environment.py`, `occa --version`, and `occa --help`. Check the EMCC extract bundle version and the work directory's `emcc_sizing_extracts/` CSV/TXT files.
2. Run `scripts/inspect_emcc_extract.py <work_dir>` and inspect extract errors and completeness. Then run `occa --pre-flight` and review the target status reports.
3. Run `occa --create-properties`. Copy each generated `*_original.csv` to its editable name when missing. Back up editable files before changes.
4. Apply `occa --copy-db-name` for Data Guard defaults, then review its source and scope. Set customer cohorts, exclusions, overrides, and approved substitutions in properties. `occa --copy-sizing` is for carrying forward prior EMCC sizing properties when applicable; `--copy-db-size` is deprecated in the guide.
5. Run `occa --add-properties` and `occa --run-metric-analysis`. Use `--checkmetrics` with the analysis command when investigating metrics. On missing metric errors, read `references/missing-metrics.md`, inspect `metric_presence_by_stage.csv` and the named property rows, and use `scripts/find_missing_metric_candidates.py <work_dir>` to gather substitution evidence. Resolve the missing metrics and rerun both commands.
6. Run `scripts/verify_occa_outputs.py <work_dir>` and review `databases.csv`, `instances.csv`, `servers.csv`, cohort rollups, plots, and exclusions. Use `scripts/generate_occa_summary_report.py` when a local summary is useful. Run `occa --emcc-import` only when the sizing is ready for upload review. `occa --reports` and `--create-artifacts` are optional report and support outputs.

Read `references/workflow.md` for file paths and checks. Read `references/cohort-policy.md` before provisional cohort assignment.

## AWR Miner route

Use the matched OCCA AWR Miner `26.9.1` scripts. Read `references/awr-workflow.md` for the collection variants, timezone and cohort properties, parse exclusions, overlap review, and import checks. The supported local sequence is `occa --awr-parse`, `occa --awr-plot`, `occa --awr-run`, then `occa --awr-import` after review. `--awr-easy` combines parse and plot, but the separate commands make intermediate review easier.
