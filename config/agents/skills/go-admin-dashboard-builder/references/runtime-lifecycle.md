# Runtime Lifecycle

Use this reference when the task is about core vs `quickstart`, boot order, dashboard route ownership, or deciding whether the dashboard page should be SSR, JSON-only, or quickstart-owned.

## Canonical Sources

- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/routing/*`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/docs/GUIDE_ROUTING.md`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/README.md`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/internal/boot/step_dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/admin/boot_bindings_dashboard.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/quickstart/ui_routes.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/main.go`

Policy order for routing work:

1. `admin/routing/*`
2. `docs/GUIDE_ROUTING.md`
3. example host wiring

## First Questions

1. Is the host already using `admin.New(...)` or `quickstart.NewAdmin(...)`?
2. Does the host want the boot-owned dashboard page at `/.../dashboard`, or the quickstart UI page at the admin base path?
3. Where can providers, areas, modules, and renderer be registered before `adm.Initialize(...)`?
4. Which admin base path and API base path are already canonical in `Config` and `Config.URLs`?

## Hard Facts

- Build config first, then `admin.New(...)` or `quickstart.NewAdmin(...)`, then register modules, providers, areas, and renderer, then call `adm.Initialize(...)`.
- `Initialize(...)` is the boot boundary that mounts dashboard routes.
- Boot-owned dashboard HTML only exists when `Dashboard.HasRenderer()` returns true.
- Boot-owned dashboard JSON routes exist when `FeatureDashboard` is enabled.
- Treat `Config.URLs` as canonical if the host has custom admin/public/API roots.

## Route Owner Rules

- Boot step mounts:
  - dashboard HTML at `dashboard.page` when a renderer exists
  - dashboard JSON at admin API `dashboard`
  - preferences/config GET and POST at `dashboard.preferences` and `dashboard.config`
  - diagnostics at `dashboard.debug`
- `quickstart.RegisterAdminUIRoutes(...)` can also mount a dashboard UI page.
- `quickstart.RegisterAdminUIRoutes(...)` is only a partial HTML surface. It does not mount content-entry panel HTML, roles HTML, or settings HTML.
- Content-entry panel HTML routes come from `quickstart.RegisterContentEntryUIRoutes(...)`.
- Roles HTML routes come from `quickstart.RegisterRolesUIRoutes(...)`.
- Settings HTML routes come from `quickstart.RegisterSettingsUIRoutes(...)`.
- Preferences may be module-owned and register their own routes during module load.
- If a host needs cookie-backed browser protection for admin HTML routes, prefer the package-managed `ProtectedBrowserRoute(...)` path. Do not add a parallel custom CSRF wrapper unless you are intentionally changing the package contract and tests.
- In `examples/web/main.go`, that quickstart dashboard page is disabled so `/admin/dashboard` remains the SSR dashboard route and `/admin` redirects there.
- Use quickstart when the host already depends on quickstart helpers or wants quickstart defaults.
- Use core when the host already owns router/runtime wiring and does not need quickstart page helpers.
- If the host already uses the boot-owned `/.../dashboard` route, disable quickstart’s dashboard UI route instead of registering both.
- Do not add ad hoc host handlers for dashboard JSON or preferences when boot already owns them.
- Treat dashboard preference/config POSTs as unsafe browser writes when called from a session-backed admin page. Keep the route owner stable, but also verify the browser client sends the CSRF token expected by the shared admin shell.
- In quickstart hosts, concrete canonical content-entry routes must be registered before generic `/content/:name/*` routes. Otherwise paths like `/admin/content/documents/new` can be consumed by the generic matcher and break the intended browser handler.
- Do not seed or keep menu links for non-dashboard pages unless their HTML owners are mounted. Otherwise auth succeeds and menu clicks 404.
- Manifest review is mandatory for route-shape changes.
- The canonical diagnostics surfaces are in-process:
  - `adm.RoutingReport()`
  - `adm.RoutingPlanner().Manifest()`
  - `routing.DiffManifests(before, after)`

## Checks

- Confirm `FeatureDashboard` is enabled where required.
- Confirm provider, area, renderer, and module registration happen before `Initialize(...)`.
- Confirm the chosen HTML page owner is unique.
- Confirm every menu-exposed non-dashboard page has an HTML owner, not just an API binding.
- Confirm the admin base path and API base path come from config, not hardcoded assumptions.
- If dashboard HTML, hydration, or shell wiring changed, confirm cookie-backed browser POSTs to dashboard preferences/config still include CSRF via `meta[name="csrf-token"]` and the shared browser helper path.
- If routes, route keys, slugs, or page ownership changed, inspect `adm.RoutingReport()`.
- Capture `adm.RoutingPlanner().Manifest()` in tests or fixtures for route-shape changes.
- Use `routing.DiffManifests(...)` to summarize added, removed, or moved routes in review.
