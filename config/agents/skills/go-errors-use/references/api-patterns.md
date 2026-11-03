# API Patterns

## Import

Always alias the package to avoid colliding with the standard library:

```go
import gerrors "github.com/goliatone/go-errors"
```

## Basic Structured Error

```go
return gerrors.New("user not found", gerrors.CategoryNotFound).
	WithCode(gerrors.CodeNotFound).
	WithTextCode("USER_NOT_FOUND").
	WithMetadata(map[string]any{"user_id": userID})
```

## Wrapping Foreign Errors

```go
if err != nil {
	return gerrors.Wrap(err, gerrors.CategoryExternal, "payment provider request failed").
		WithCode(502).
		WithTextCode("PAYMENT_PROVIDER_ERROR")
}
```

`Wrap` preserves an existing `*gerrors.Error` by cloning it and prepending the message. It does not recategorize that error.

## Validation

```go
return gerrors.NewValidation("invalid request",
	gerrors.FieldError{Field: "email", Message: "must be a valid email"},
	gerrors.FieldError{Field: "password", Message: "is required"},
).WithCode(400).WithTextCode("VALIDATION_ERROR")
```

For ozzo-validation:

```go
if err := req.Validate(); err != nil {
	return gerrors.FromOzzoValidation(err, "invalid request").
		WithCode(400).
		WithTextCode("VALIDATION_ERROR")
}
```

## HTTP Response

```go
var ge *gerrors.Error
if stdErrors.As(err, &ge) {
	resp := ge.ToErrorResponse(false, nil)
	writeJSON(w, ge.Code, resp)
	return
}
```

When `Code` may be unset, use a local category-to-status helper or `MapToError` with project mappers.

## Error Mapper

```go
func mapProviderError(err error) *gerrors.Error {
	var providerErr ProviderError
	if stdErrors.As(err, &providerErr) {
		return gerrors.New(providerErr.Message, gerrors.CategoryExternal).
			WithCode(providerErr.Status).
			WithTextCode("PROVIDER_ERROR")
	}
	return nil
}

mapped := gerrors.MapToError(err, []gerrors.ErrorMapper{
	mapProviderError,
})
```

## Logging

```go
attrs := gerrors.ToSlogAttributes(err)
logger.LogAttrs(ctx, slog.LevelError, "request failed", attrs...)
```

Or let severity choose the level:

```go
if ge, ok := err.(*gerrors.Error); ok {
	gerrors.LogBySeverity(logger, ge)
}
```

## Collector

Use a collector when many independent checks can fail:

```go
collector := gerrors.NewCollector(gerrors.WithMaxErrors(50))

if req.Email == "" {
	collector.AddValidation("email", "is required")
}
if err := checkInventory(ctx, req.Items); err != nil {
	collector.Add(gerrors.Wrap(err, gerrors.CategoryExternal, "inventory check failed"))
}

if collector.HasErrors() {
	return collector.Merge()
}
```

Do not use `ErrorCollector` for single-error control flow.
