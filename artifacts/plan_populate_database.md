# Database Population Plan

## Objective

Populate the SQLite database from the sample `VN30.json` payload.

## Scope

1. Add configuration for the local sample payload path.
2. Implement ingestion helpers to parse `VN30.json` into `VN30Record` objects.
3. Add batch upsert support in the DAO.
4. Implement a runnable entrypoint that initializes and populates the database.

## Constraints

- Use the existing narrowed schema only.
- Keep timestamps stored as ISO 8601 text.
- Prefer idempotent inserts so repeated runs do not create duplicates.
