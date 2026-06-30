# OCCA Project Context

## Purpose

Oracle Cloud Capacity Analytics (OCCA) supports comparative sizing for Oracle database migrations. It uses source workload history to estimate future-state resource requirements for Oracle Cloud platforms.

## Resource Model

OCCA is database-centric and consumption-based. The key resource categories are:

- CPU consumption, measured as vCPU and later expressed as OCPU/ECPU where relevant.
- Memory consumption.
- I/O consumption.
- Storage allocation, used space, and working set considerations.

The guide emphasizes time-aligned peaks for cohorts rather than simple sum-of-peaks sizing. This matters when databases are consolidated because databases peak at different times.

## EMCC Data

EMCC extracts gather:

- Inventory of databases, PDBs, hosts, and relationships.
- Database resource consumption metrics.
- Host/system utilization metrics used in limited attenuation/debugging cases.
- Availability and target health data.
- Daily metrics for longer history and hourly metrics for finer-grained sizing.

The guide states EMCC extracts can include about 33 days to 3 months of hourly data and up to 12 months of daily data, subject to customer EMCC history and target health.

## AWR Miner Data

OCCA AWR Miner extracts one database at a time from AWR history. It is useful when EMCC is unavailable or incomplete, but it usually has less historical coverage. Snapshot overlap and timezone correctness are critical for cohort sizing.

## Cohorts

Cohorts are groups of databases that may be consolidated together. Cohort decisions are customer decisions and should reflect isolation needs such as:

- Physical location.
- Administrative separation.
- Security separation.
- Blast radius.
- Maintenance separation.
- Noisy-neighbor concerns.

Common starting cohorts may include site and lifecycle splits such as `SITE1-PROD`, `SITE1-NON-PROD`, `SITE2-PROD`, and `SITE2-NON-PROD`, but actual cohort definitions must come from the customer/user.

## Missing Metrics

Do not edit raw extracts to fix missing data. Use generated property files:

- `occa_sizing_properties/properties_database.csv`
- `occa_sizing_properties/properties_instance.csv`
- `occa_sizing_properties/properties_server.csv` when needed
- AWR equivalents under `awr_miner_occa/properties`

Missing metrics may be caused by old EMCC/agent versions, EM jobs, disabled job queues, targets in bad status, stale metrics, disabled metric collection, standby databases, or extract execution errors.

All substituted values and exclusions should be auditable and customer-approved.

## Data Guard

Standby databases often have missing or stale metrics. `occa --copy-db-name` sets default copy directives based on primary/standby relationships. Review these before final sizing.

Important property columns include:

- `Use Values from Database Name`
- `Use Values Scope`
- `Use Values Pct`

The default physical standby behavior uses a lower percentage of primary consumption for normal operation and full primary consumption for disaster operation, but this must be validated against the customer's intended standby workload.

