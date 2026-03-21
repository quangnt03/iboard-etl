# Three-Tier Refactor Plan

## Objective

Refactor the current SQLite population flow into an explicit 3-tier architecture similar to Spring Boot.

## Target Layers

- `controller`: data representation and external interface orchestration
- `service`: business logic for validation and fetching/loading data
- `repository`: SQLite DAO and persistence concerns

## Scope

1. Update `AGENTS.md` with the 3-tier architecture rule.
2. Create controller, service, and repository modules under `src/`.
3. Move DAO code into the repository layer.
4. Move payload loading and validation into the service layer.
5. Move entrypoint orchestration into the controller layer.
6. Keep current behavior intact: load `VN30.json` into SQLite.

## Constraints

- Preserve the narrowed VN30 schema.
- Avoid destructive file moves that could break current imports without a compatibility path.
- Keep the refactor small and readable.
