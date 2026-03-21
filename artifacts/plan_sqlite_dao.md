# SQLite DAO Plan

## Objective

Add a reusable SQLite connection layer and DAO for the narrowed `vn30_stock` table.

## Scope

1. Define database-related configuration values.
2. Initialize SQLite with `sql/schema.sql`.
3. Implement DAO methods for create, read, update, delete, and list operations.
4. Keep Python types aligned with `src/schemas.py`.

## Decisions

- Use the standard-library `sqlite3` module.
- Store timestamps as ISO 8601 text in SQLite.
- Use `VN30Record` as the main DAO payload model.
- Keep DAO operations focused on the current table only.

## Deliverables

- Updated `src/config.py`
- Implemented `src/db.py`
- Updated `tasks/todo.md`
