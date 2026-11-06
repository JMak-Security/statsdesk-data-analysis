# Reproducing the analysis

1. From the project root, run `statsdesk analyze` to use the checked-in local snapshot.
2. Confirm the command accepts the CSV only when its SHA-256 matches
   `data/dataset_metadata.json`.
3. Review the counts and exclusions before interpreting the descriptive results.
4. To refresh, run `statsdesk fetch --output-dir data`, inspect the changed snapshot and metadata,
   then rerun `statsdesk analyze`.
5. Record the new digest and retrieval metadata with any report shared outside the project.
6. Do not compare refreshed and checked-in results as though they were identical dataset versions.

For interpretation, refer to the committed pre-analysis plan. Do not describe association as
causation, and do not infer individual outcomes from country-level records.
