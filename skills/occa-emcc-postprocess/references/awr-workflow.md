# OCCA AWR Miner workflow (26.9.1)

Use the matched `AWR-Miner-26.9.1.zip` for collection. Place unmodified `awr-hist-<DBID>-<DBNAME>-<BEGIN>-<END>.out` files in `<work_dir>/awr_miner_out/`; filenames carry identity and snapshot range. Preserve the original archive and outputs. The customer script readme and Extracts User Guide in the bundle describe SQL*Plus prerequisites and collection.

## Collection choice

- `awr_miner.sql` collects a CDB/root or non-CDB as one database. `awr_miner_lite.sql` is the lighter collection variant; confirm its coverage meets sizing needs before using it.
- `awr_pdb_miner.sql` collects a PDB as its own database when separate PDB sizing is required. Run it against the PDB service. For 19c and earlier, check `AWR_PDB_AUTOFLUSH_ENABLED` and snapshot interval: without local snapshots, CPU and IOPS history can be too sparse. Per-container metrics require Oracle 12.2 or later; 12.1 yields storage only.
- The 26.9.1 parser recognizes standalone PDB output. Do not combine CDB and PDB measurements as one workload or add their CPU/IO metrics together; CDB plus PDB integration is not shipped.

## Local processing

From `<work_dir>`:

```bash
occa --awr-parse
occa --awr-plot
```

Review parse warnings and `<work_dir>/awr_excluded_databases.csv` if created. It records files excluded during parsing; a nonfatal warning does not necessarily exclude a file. OCCA may repair narrow missing SGA cases from adjacent same-instance rows or SGA advice; inspect the warning and resulting values. Do not edit the `.out` file to force parsing.

Copy generated `awr_miner_occa/properties/awr_tz_database_original.csv` and `awr_properties_database_original.csv` to the corresponding editable names if missing. Back up existing editable files. Set the time zone for every database in `awr_tz_database.csv` and customer-approved cohorts in `awr_properties_database.csv`. Then run:

```bash
occa --awr-run
```

Review `awr_miner_occa/sizing/databases.csv`, `instances.csv`, cohort rollups, and plots for exclusions, reasonableness, and snapshot coverage overlap. The guide recommends cohort extracts collected within about two days of each other and rejects snapshot intervals longer than one hour. AWR retention and overlapping coverage determine confidence in consolidated sizing.

After the results are ready for upload review, run `occa --awr-import` and verify a zero exit status and `awr_miner_occa/awr_occa_upload_data.json`. In 26.9.1, import returns nonzero when it refuses to build a payload, including unresolved exclusions, missing sizing files, or parsed output. Never infer success from a prior JSON file alone; check its modification time or run it in a clean work directory. `occa --awr-reports` is optional.
