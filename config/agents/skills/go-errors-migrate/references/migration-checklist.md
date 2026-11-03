# Migration Checklist

## Inventory

Search for:

```bash
rg "fmt\\.Errorf|errors\\.New|type .*Error|StatusCode\\(|Unwrap\\(|errors\\.Is|errors\\.As|validation\\.Errors|slog\\."
```

Identify:

- API response conversion points
- validation entry points
- custom domain errors
- external service adapters
- retry loops
- logging middleware
- tests asserting error strings or response JSON

## Mapping Policy

Create or infer a small policy before editing:

- `CategoryValidation`: client input and field-level failures
- `CategoryAuth`: authentication failures
- `CategoryAuthz`: authorization/permission failures
- `CategoryNotFound`: missing resources
- `CategoryConflict`: uniqueness/state conflicts
- `CategoryRateLimit`: throttling
- `CategoryBadInput`: malformed client input
- `CategoryExternal`: dependency/provider failures
- `CategoryInternal`: unexpected system failures
- `CategoryOperation`: business operation failures without a better category

Prefer stable uppercase `TextCode` values for client-facing conditions.

## Refactor Sequence

1. Add the dependency and alias import as `gerrors`.
2. Normalize API error responses at one boundary.
3. Convert validation errors to `NewValidation`, `FromOzzoValidation`, or collectors.
4. Add `ErrorMapper`s for existing domain/framework errors.
5. Wrap external dependency failures at adapters.
6. Add collectors only for workflows that can produce multiple independent errors.
7. Add retryable errors only when retry policy consumes them.
8. Enrich logging with `ToSlogAttributes` or `LogBySeverity`.

## Stop Conditions

Stop and reassess before:

- rewriting all internal errors mechanically
- changing public error strings used by tests or callers
- deleting sentinel or typed errors used by `errors.Is` or `errors.As`
- adding metadata that may contain secrets or large payloads
