# AI-OCCA Notes

## Current Status

- Project repository path: `/Users/PWSTEPHE/codex/AI-OCCA`
- Initialized Codex project files:
  - `AGENTS.md`
  - `README.md`
  - `.codex/OCCA_CONTEXT.md`
  - `.codex/OCCA_AUTOMATION_PLAN.md`
- Source artifacts present:
  - `OCCA_User_Guide.pdf`
  - `Customer_emcc_sizing_extracts-26.2.0.zip`
  - `occa-26.3.0-py3-none-any.whl`

## Key Observations

- OCCA is a comparative sizing workflow for Oracle database workloads moving to Oracle Cloud.
- EMCC extracts are the primary source for inventory, resource consumption, and longer historical trends.
- OCCA AWR Miner extracts are supported but usually provide shorter historical windows and require careful timezone/snapshot-overlap handling.
- Raw extract data should be preserved; sizing corrections should be made through generated property files.
- Cohort assignment, exclusions, Data Guard directives, and missing-metric substitutions require user/customer decisions.

## Next Working Session

- Decide where customer working directories should live.
- Create or choose a Python virtual environment strategy.
- Install `occa-26.3.0-py3-none-any.whl`.
- Capture `occa --help` and `occa --version`.
- Point Codex to the customer extract zip and begin intake validation.

## Open Questions

1. Where should customer processing folders be created by default?
2. Should each customer run get its own virtual environment, or should OCCA use a shared local tool environment?
3. What naming convention should be used for customer/opportunity folders?
4. What default cohort model should be used if the customer has not supplied one?
5. Which Oracle Cloud target platforms should the first automation optimize for?

