# Widgets And Contracts

Use this reference when the task adds or changes dashboard widgets, provider specs, widget config decoding, or payload shapes.

## Canonical Sources

- `$HOME/Development/GO/src/github.com/goliatone/go-admin/docs/GUIDE_DASHBOARD_WIDGETS.md`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/dashboard_payload.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/setup/dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/setup/dashboard_contract.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/commerce/dashboard.go`

## Choose The Pattern First

- Use `examples/commerce/dashboard.go` when you only need one or two widgets with simple inline payload structs.
- Use `examples/web/setup/dashboard.go` plus `dashboard_contract.go` when the host needs:
  - typed config structs
  - reusable payload contracts
  - provider overrides
  - custom scoped areas
  - validation of canonical payload keys

## Procedure

1. Get the dashboard handle with `adm.Dashboard()`.
2. Register custom areas first if the provider uses a non-shared area.
3. Define a stable `DashboardProviderSpec.Code`.
4. Set `DefaultArea` only when a default widget instance should be seeded automatically.
5. Use `DefaultConfig` for canonical defaults and decode into a typed config struct with `admin.DecodeWidgetConfig[T](...)`.
6. Keep the handler thin and return `admin.WidgetPayloadOf(...)` from a typed payload struct.

## Hard Facts

- `Dashboard.RegisterProvider(...)` replaces an existing provider with the same `Code`.
- Re-registering a provider also clears prior default instances for that code.
- If an override omits `DefaultArea`, it suppresses automatic default widget creation for that provider.
- `DefaultConfig` is merged with persisted instance config at runtime.
- If `CommandName` is set and the command bus is wired, the dashboard registers a provider command hook.

## Contract Rules

- Payload roots must be structs or pointers to structs.
- `admin.DecodeWidgetConfig[T](...)` rejects unknown fields. Do not rely on loose map decoding when config should be stable.
- Keep payloads JSON-only. Do not emit HTML fragments or legacy chart HTML keys.
- Define payload structs before changing templates or client code so server and client stay aligned.
- Use a separate contract file only when more than one provider or template consumer depends on the same payload shape.
- Do not branch payload shape by render mode.
- If widget hydration adds mutating browser requests, use the shared browser helper or equivalent header injection so unsafe same-origin writes carry `X-CSRF-Token`.

## Checks

- Provider code is stable and unique.
- Widget config decoding fails clearly on bad input.
- Payload contract matches the renderer or client expectation.
- The widget only appears by default when `DefaultArea` is intentional.
- Provider overrides do not leave duplicate default widgets behind.
- Add contract tests for required keys and canonical payload shape.
- If template output changed, add or update SSR regression coverage.
- If client rendering or hydration changed, add or update hydration regression coverage.
- If client rendering or hydration now writes back to the server, add or update a browser-write regression that exercises the CSRF path for the dashboard shell.
