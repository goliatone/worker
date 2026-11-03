# Compatibility Tests

Add focused tests for behavior that callers observe.

## Standard Error Compatibility

```go
wrapped := gerrors.Wrap(ErrNotReady, gerrors.CategoryOperation, "operation failed")

if !stdErrors.Is(wrapped, ErrNotReady) {
	t.Fatal("expected errors.Is compatibility")
}
```

For typed errors:

```go
var target *ProviderError
if !stdErrors.As(err, &target) {
	t.Fatal("expected errors.As compatibility")
}
```

## Structured Fields

Assert category, code, and text code:

```go
var ge *gerrors.Error
if !stdErrors.As(err, &ge) {
	t.Fatal("expected structured error")
}
if ge.Category != gerrors.CategoryValidation {
	t.Fatalf("category = %s", ge.Category)
}
if ge.Code != 400 {
	t.Fatalf("code = %d", ge.Code)
}
if ge.TextCode != "VALIDATION_ERROR" {
	t.Fatalf("text_code = %s", ge.TextCode)
}
```

## Validation Payload

```go
fields := ge.ValidationMap()
if fields["email"] == "" {
	t.Fatal("expected email validation error")
}
```

## API JSON

Test response shape rather than raw string equality when possible:

```go
resp := ge.ToErrorResponse(false, nil)
body, err := json.Marshal(resp)
if err != nil {
	t.Fatal(err)
}

var decoded struct {
	Error struct {
		Category string `json:"category"`
		TextCode string `json:"text_code"`
		Message  string `json:"message"`
	} `json:"error"`
}
if err := json.Unmarshal(body, &decoded); err != nil {
	t.Fatal(err)
}
```

## Collector Behavior

For batch workflows, assert merged category, highest severity, and validation aggregation.
