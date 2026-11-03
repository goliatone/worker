# Rendering And Placements

Use this reference when the task affects dashboard templates, renderers, areas, or layout placement.

## Canonical Sources

- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/dashboard_renderer.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/quickstart/dashboard_renderer.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/quickstart/dashboard_placements.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/setup/dashboard_renderer.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/setup/dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/commerce/dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/setup/dashboard_placements_test.go`

## Renderer Rules

- Prefer the existing dashboard renderer unless the task explicitly needs a new template source or template function set.
- In quickstart-based hosts, use `quickstart.WithDefaultDashboardRenderer(...)` for stock SSR or `quickstart.NewDashboardTemplateRenderer(...)` for explicit template control.
- `WithDefaultDashboardRenderer(...)` is safe when a renderer already exists because it skips replacement.
- If embedded templates are disabled, you must provide a template FS or renderer creation fails.
- Custom renderers implement `admin.DashboardRenderer` and accept `admin.AdminDashboardPage`. The stock quickstart renderer rejects arbitrary map payloads.
- `quickstart.NormalizeDashboardTemplateData(...)` accepts a raw typed `dashboard.Page` only at the template-adapter compatibility boundary; it does not broaden the renderer interface.
- `quickstart.DashboardTemplatesFS()` returns `client.Templates()`. The compact quickstart dashboard document was removed and is not a fallback; caller filesystems are first-wins overlays on the canonical packaged stack.
- Build dashboard header/breadcrumb/navigation presentation through
  `admin.AdminPageChrome` and `admin.EnrichLayoutViewContextWithChrome`; the
  dashboard template must not shadow typed title fields or add another shell.
- Keep renderer changes in admin setup code, not widget providers.
- No renderer means no boot-owned dashboard HTML route; JSON remains the fallback surface.
- If you override the dashboard shell or template stack, preserve `csrf_meta` in the page head and `csrf_field` in any custom browser form that posts back through the admin session.
- Consume shared browser presentation from the generated
  `@goliatone/go-admin-client/components.css` export. Load namespaced product
  CSS afterward via the host asset filesystem; do not copy go-admin component
  sources or import package `src/` paths.

## Placement Rules

- Use `quickstart.ResolveDashboardArea(...)` for standard main/sidebar/footer mapping in quickstart-based hosts.
- Use `RegisterArea(...)` for custom scoped areas such as detail-page widget zones.
- Register custom areas before providers that use those areas.
- Remember that `DefaultArea` controls where default widgets seed, and user layout/preferences are keyed by area code.
- Treat placement and area decisions as admin composition concerns, not business logic.

## Pattern Selection

- Use `examples/commerce/dashboard.go` for minimal placement-aware provider registration.
- Use `examples/web/setup/dashboard_renderer.go` and `examples/web/setup/dashboard.go` when you need:
  - template overrides
  - template func overrides
  - main/sidebar placement mapping
  - custom detail or scoped areas
  - built-in provider overrides without duplicate defaults

## Checks

- Renderer still loads the expected templates.
- Widgets resolve to the intended area.
- Custom areas are registered before widgets depend on them.
- Placement defaults do not unintentionally create duplicate widgets.
- If placement mapping changed, add or update a provider-area assertion like `examples/web/setup/dashboard_placements_test.go`.
- If rendering behavior changed, add or update SSR regression coverage and client hydration coverage where applicable.
- For shell/component changes, exercise the downstream extension contract or
  equivalent proof of one document/shell owner, typed page chrome, bounded
  structural overrides, public component delivery, theme propagation, and
  product asset mounting.
- If rendering or hydration changes introduce unsafe same-origin writes, verify the dashboard shell still exposes the CSRF token and that the client path sends `X-CSRF-Token`.
