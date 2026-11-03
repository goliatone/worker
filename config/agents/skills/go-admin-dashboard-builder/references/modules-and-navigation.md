# Modules And Navigation

Use this reference when the task adds a dashboard page, custom dashboard section, menu item, or route contract.

## Canonical Sources

- `$HOME/Development/GO/src/github.com/goliatone/go-admin/docs/GUIDE_MODULES.md`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/docs/GUIDE_ROUTING.md`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/examples/web/modules.go`
- `$HOME/Development/GO/src/github.com/goliatone/go-admin/README.md`

## Keep These Pieces Together

1. `Manifest()`
2. `Register(...)`
3. `RouteContract()`
4. `MenuItems(...)`

## Procedure

- Use `Manifest()` to declare module identity and dashboard feature gating.
- Use `Register(...)` only for module-local setup.
- Use `RouteContract()` to declare the relative UI route table for the module.
- Use `MenuItems(...)` to point navigation at the dashboard path that matches that route contract under the current admin base path.
- Mounted dashboard modules should follow the `RouteContractProvider` contract from `GUIDE_MODULES.md` and the relative-route rules from `GUIDE_ROUTING.md`.

## Guardrails

- Keep dashboard route slugs stable once links, tests, or menu keys depend on them.
- Feature-gate dashboard modules with `FeatureDashboard`.
- Preserve label keys when translations exist.
- If the module menu uses a raw path built from `basePath`, verify it still matches the route contract path.
- If the task only changes navigation, still verify the route contract, menu `Target.path`, and active menu key remain consistent.
- Route contract and menu target agreement is necessary but not sufficient for non-dashboard pages. Also verify the host mounted the HTML route owner for every menu-exposed page.
- If a page reuses the shared sidebar partial, verify both primary nav and utility nav context are supplied so the shell stays consistent across route owners.
- If a module-owned dashboard page reuses the shared admin shell and performs browser writes, preserve the shell CSRF contract (`csrf_meta` in layout, `X-CSRF-Token` on unsafe same-origin requests).
- If a menu target lands on a quickstart-owned canonical content page, verify the concrete canonical route wins over any generic `/content/:name/*` matcher so `/new`, detail, and edit flows resolve to the intended handler.

## Repo Pattern

- `examples/web/modules.go` uses:
  - `Manifest()` with `FeatureDashboard`
  - `RouteContract()` with a stable `dashboard.index` key mapped to `"/dashboard"`
  - `MenuItems(...)` that points at `path.Join("/", basePath, "dashboard")`
- Copy that full pattern when adding a dashboard module. Do not change only one piece.

## Checks

- Manifest ID, feature flags, route slug, route key, and menu key are stable.
- Menu target path matches the actual dashboard route path.
- Parent menu and position are intentional.
- The dashboard route is not being defined twice in different modules or host handlers.
- If route shape changed and no manifest-oriented assertion changed, treat that as incomplete verification.
