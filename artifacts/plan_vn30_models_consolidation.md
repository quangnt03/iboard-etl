# VN30 Models Consolidation Plan

## Objective

Consolidate VN30 domain models from separate API, repository, service, and controller files into a single domain model module under `src/models/`.

## Scope

1. Create one VN30 domain model file containing API, DAO, service-result, and controller-response models.
2. Update repository, service, controller, ingest, tests, and package exports to import from the new module.
3. Keep `AppConfig` in its own file because it is application-wide configuration, not a VN30 domain model.
4. Preserve runtime behavior and test coverage.

## Constraints

- Do not change the current VN30 field schema.
- Keep compatibility minimal and avoid duplicate model definitions.
- Verify the consolidation with the existing unit test suite.
