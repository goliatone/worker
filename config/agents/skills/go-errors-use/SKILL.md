---
name: go-errors-use
description: Use github.com/goliatone/go-errors in Go projects. Trigger when adding structured categorized errors, API error responses, validation errors, slog attributes, retryable errors, error categories, text codes, or error mappers using go-errors in new or existing Go code.
---

# Go Errors Use

## Overview

Use `go-errors` as a structured error contract at meaningful project boundaries. Do not mechanically replace every ordinary Go error; introduce categories, codes, text codes, metadata, validation details, retry semantics, and logging attributes where callers or clients benefit from that structure.

## Workflow

1. Inspect the project first:
   - error creation and wrapping style
   - HTTP/API response helpers
   - validation library
   - logging setup
   - retry logic
   - existing domain error types or sentinel errors

2. Import the package with an alias:

```go
import gerrors "github.com/goliatone/go-errors"
```

3. Add structured errors at boundaries:
   - HTTP handlers and middleware
   - service/domain returns that must be interpreted by callers
   - validation conversion
   - external service adapters
   - batch/workflow processing
   - structured logging points

4. Keep compatibility with standard Go error handling:
   - use `errors.Is` and `errors.As` for existing sentinels and typed errors
   - wrap foreign errors instead of discarding them
   - avoid hiding the original cause unless the boundary intentionally normalizes it

## Constructor Rules

- Use `gerrors.New(message, category)` for new structured errors.
- Use `gerrors.Wrap(err, category, message)` for foreign errors.
- Use `gerrors.NewValidation(...)` for field-level validation failures.
- Use `gerrors.FromOzzoValidation(...)` or `gerrors.ValidateWithOzzo(...)` when ozzo-validation is already used.
- Use `gerrors.NewRetryable...` only when callers inspect retryability.
- Add `WithCode`, `WithTextCode`, `WithMetadata`, `WithRequestID`, and `WithSeverity` at boundaries where clients, logs, or retry policy need them.

## Boundary Patterns

- For API responses, return `ErrorResponse` values with stack traces disabled by default.
- For validation, preserve field names and client-safe messages.
- For logging, use `gerrors.ToSlogAttributes(err)` or `gerrors.LogBySeverity(logger, err)`.
- For batch operations, use `gerrors.NewCollector(...)` only when multiple failures are expected.
- For project/framework errors, define `gerrors.ErrorMapper` functions near the boundary that performs normalization.

## Verification

- Add or update tests for category, numeric code, text code, validation payload, and HTTP status behavior.
- Test `errors.Is` and `errors.As` compatibility when existing callers depend on it.
- Run the repository's normal Go test command, usually `go test ./...`.

## References

- Read `references/api-patterns.md` when implementing HTTP/API, validation, logging, retry, or mapper examples.
- Read `references/current-caveats.md` before relying on less common APIs or README-only claims.
