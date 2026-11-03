# Custom Mappers

Use `ErrorMapper`s to normalize existing project, framework, or dependency errors without forcing deep rewrites.

## Typed Error Mapper

```go
func mapProviderError(err error) *gerrors.Error {
	var providerErr ProviderError
	if stdErrors.As(err, &providerErr) {
		return gerrors.New(providerErr.Message, gerrors.CategoryExternal).
			WithCode(providerErr.StatusCode).
			WithTextCode("PROVIDER_ERROR")
	}
	return nil
}
```

## StatusCode Interface Mapper

The package includes `MapHTTPErrors`, which recognizes errors implementing:

```go
interface{ StatusCode() int }
```

Use it when framework errors expose status codes.

## Project Mapper List

```go
func projectErrorMappers() []gerrors.ErrorMapper {
	return []gerrors.ErrorMapper{
		mapProviderError,
		mapDomainConflict,
		gerrors.MapHTTPErrors,
	}
}

func normalizeError(err error) *gerrors.Error {
	return gerrors.MapToError(err, projectErrorMappers())
}
```

## String Matching

String matching is acceptable only at integration boundaries where no typed signal exists. Keep it narrow and covered by tests.

## Preserve Standard Behavior

Keep sentinel and typed errors when callers rely on:

```go
stdErrors.Is(err, ErrThing)
stdErrors.As(err, &target)
```

Wrap them with `gerrors.Wrap` rather than replacing them too early.
