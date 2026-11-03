# Current Caveats

- Import as `gerrors`; plain `errors` conflicts with the Go standard library.
- `New` captures location and defaults severity to `SeverityError`.
- Validation constructors currently build `Error` directly. Add severity or location manually if the project depends on those fields.
- `Wrap` preserves existing `*gerrors.Error` category/location by cloning and prepending the message. It is not a recategorization helper for already-structured errors.
- `RetryableError` currently exposes `RetryDealy(attempt int)` with that spelling. Do not call `RetryDelay` unless the installed package has been fixed.
- `ErrorCollector.AddRetryable` stores the base `*Error`; collector retry filtering is severity-based after collection.
- Location capture is controlled by `GO_ERRORS_DISABLE_LOCATION=true`, `SetLocationCapture(false)`, or `SetLocationCapture(true)`.
- The README mentions production build tags, but the current implementation does not include build-tag config files.
- `IsDevelopment` exists but is not currently wired into response behavior.
- `ToSlogAttributes` does not currently include location, even though the README text says it does.
