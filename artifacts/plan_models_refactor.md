# Models Refactor Plan

## Objective

Move all Pydantic models into `src/models/` with one file per domain while keeping the current 3-tier runtime behavior intact.

## Scope

1. Create `src/models/` package and separate model files by domain.
2. Move API, config, repository, service, and controller response models into that package.
3. Convert `src/config.py` into a config loader that uses the new config model.
4. Update imports across controller, service, repository, ingest, and tests.
5. Keep compatibility exports where helpful to avoid unnecessary breakage.

## Constraints

- Preserve the current narrowed VN30 schema and behavior.
- Do not change persistence logic beyond import/model relocation.
- Keep tests runnable after the refactor.
