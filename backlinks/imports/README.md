# Imports (Step 4)

This folder is for manually exported backlink CSV files.

## Structure

- `imports/inbox/` — place fresh CSV exports here before import.
- `imports/processed/` — move CSV files here after successful import.
- `imports/samples/` — sample CSV formats you can copy.

## Assumptions

- Imports are local CSV files only.
- No scraping and no external API calls.
- Source files may use different column names; the importer uses simple header aliases.
- Imported rows default to `status=new` or `status=active` based on whether the domain has been seen before in tracker history.
- Suspicious detection is still manual after import.
