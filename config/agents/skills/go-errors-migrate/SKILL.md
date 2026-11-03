---
name: go-errors-migrate
description: Refactor existing Go projects to adopt github.com/goliatone/go-errors safely. Trigger when converting fmt.Errorf, errors.New, custom error types, API error helpers, validation handling, logging, retry handling, or domain errors to structured go-errors usage.
---

# Go Errors Migrate

## Overview

Migrate existing projects to `go-errors` by introducing structure at boundaries first, preserving standard Go error behavior, and avoiding broad mechanical rewrites. Treat the package as a project error contract for categories, codes, validation payloads, metadata, logging, retry policy, and API responses.

## Workflow

1. Inventory current behavior before editing:
   - `errors.New`, `fmt.Errorf`, `%w`, and sentinel errors
   - custom typed errors and `StatusCode()` style interfaces
   - HTTP/API response helpers
   - validation conversion
   - logging middleware
   - retry decisions
   - tests that assert error strings, status codes, or JSON payloads

2. Pick adoption boundaries:
   - handler/controller response conversion
   - service/domain errors that callers inspect
   - validation layer
   - repository/external client adapters
   - batch jobs and workers
   - auth/onboarding flows

3. Add the dependency and import with an alias:

```go
import gerrors "github.com/goliatone/go-errors"
```

4. Define a local mapping policy:
   - category per failure class
   - numeric HTTP code policy
   - stable `TextCode` values
   - allowed metadata keys
   - severity conventions
   - location/stack policy by environment

5. Convert outward-facing behavior first. Avoid replacing every internal `fmt.Errorf` unless category, validation, retry, or response behavior changes.

6. Preserve compatibility:
   - keep existing sentinel errors when callers use `errors.Is`
   - keep typed errors when callers use `errors.As`
   - wrap foreign errors instead of replacing them
   - add `ErrorMapper`s where domain/framework errors need normalization

## Refactor Order

1. Normalize API response conversion.
2. Convert validation errors to `FieldError` payloads.
3. Add custom mappers for existing domain/framework errors.
4. Wrap external dependency failures at adapter boundaries.
5. Use collectors for true multi-error workflows.
6. Introduce retryable errors only where retry policy consumes them.
7. Enrich logging with `ToSlogAttributes` or severity logging.

## Guardrails

- Do not import the package as plain `errors`.
- Do not expose stack traces in production responses.
- Do not use `ErrorCollector` for single-error control flow.
- Do not store secrets, credentials, tokens, or large request bodies in metadata.
- Do not recategorize an existing `*gerrors.Error` by assuming `Wrap` changes its category.
- Do not depend on README-only APIs without checking the installed package.

## Verification

- Update tests before or alongside behavior changes.
- Assert response shape, category, code, text code, validation fields, and logging attributes where relevant.
- Keep compatibility tests for `errors.Is` and `errors.As`.
- Run the repository's normal Go test command, usually `go test ./...`.

## References

- Read `references/migration-checklist.md` before starting a migration.
- Read `references/custom-mappers.md` when existing domain/framework errors need conversion.
- Read `references/compatibility-tests.md` when updating or adding tests.
- Read `references/current-caveats.md` before relying on less common APIs or README-only claims.
