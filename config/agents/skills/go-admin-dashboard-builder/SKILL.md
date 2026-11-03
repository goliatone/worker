---
name: go-admin-dashboard-builder
description: "Build or modify go-admin dashboards only: pick core vs quickstart dashboard wiring, own dashboard routes and menu items, register typed widget providers, wire SSR renderers/templates, and place widgets in shared or custom areas."
---

# Go Admin Dashboard Builder

Use this skill only for dashboard work in `go-admin`: dashboard route ownership, dashboard modules and menu items, widget providers and payload contracts, renderers and templates, and placements or custom areas.

Do not use it for generic admin bootstrap, auth, CMS CRUD, panel design, or non-dashboard navigation. Keep product decisions in the calling skill.
If a dashboard or sidebar task exposes 404s or layout drift on non-dashboard admin pages, stop and audit host HTML-route registration first. In quickstart hosts, `RegisterAdminUIRoutes(...)` is not the whole admin UI surface.

Published guide docs are policy. Example apps and setup files are implementation patterns. When they differ in emphasis, follow the guide docs first and use examples to copy the concrete shape.

## Read Path

1. Read [references/runtime-lifecycle.md](references/runtime-lifecycle.md) first.
2. Read one task reference:
   - [references/modules-and-navigation.md](references/modules-and-navigation.md)
   - [references/widgets-and-contracts.md](references/widgets-and-contracts.md)
   - [references/rendering-and-placements.md](references/rendering-and-placements.md)
3. Read a second task reference only if the change clearly crosses that boundary.

## Decision Tree

1. Identify the host type.
   - `quickstart.NewAdminConfig(...)` + `quickstart.NewAdmin(...)`: stay in quickstart.
   - `admin.New(...)`: stay in core unless the host already opted into quickstart helpers.
2. Identify the dashboard HTML owner.
   - Boot-owned `/.../dashboard` route: do not enable quickstart’s dashboard page route.
   - Quickstart UI page at the admin base path: only use it intentionally.
3. Identify the change type.
   - Module, route contract, or menu target: read `modules-and-navigation.md`.
   - Provider, config, payload, or default widget behavior: read `widgets-and-contracts.md`.
   - Renderer, template, area, or placement: read `rendering-and-placements.md`.
4. Pick the smallest repo pattern that fits.
   - `examples/commerce/dashboard.go`: one or two simple widgets.
   - `examples/web/setup/dashboard*.go`: typed contracts, provider overrides, custom areas, or custom renderer work.

## Hard Rules

- For route policy and verification, prefer `docs/GUIDE_ROUTING.md` over examples.
- For widget contracts and testing, prefer `docs/GUIDE_DASHBOARD_WIDGETS.md` over examples.
- For shared shell, typed page chrome, and component styling, prefer
  `docs/GUIDE_VIEW_CUSTOMIZATION.md`, `docs/GUIDE_UI_PRIMITIVES.md`, and
  `docs/GUIDE_FRONTEND.md` over host template copies.
- For module-backed dashboard work, prefer `docs/GUIDE_MODULES.md` plus `docs/GUIDE_ROUTING.md` over example module code.
- Stay in quickstart when the host already uses quickstart admin construction or needs quickstart helpers such as `ResolveDashboardArea(...)`, `WithDefaultDashboardRenderer(...)`, or `RegisterAdminUIRoutes(...)`.
- Stay in core when the host already constructs `admin.New(...)` and only needs dashboard providers, areas, routes, or a renderer.
- Do not introduce quickstart UI routes just to get dashboard APIs. Core boot already mounts dashboard JSON and, when a renderer exists, the dashboard HTML route.
- Dashboard HTML ownership implies browser-write responsibility. If a dashboard page, widget, or hydrated client performs unsafe same-origin writes, preserve `csrf_meta` in the page shell and send `X-CSRF-Token` from `meta[name="csrf-token"]` or the shared browser helper.
- Do not hand-roll a parallel browser CSRF wrapper for admin HTML routes. Reuse the package-managed browser protection path so origin protection, CSRF response headers, secure-key derivation, and session-key resolution stay aligned.
- `quickstart.RegisterAdminUIRoutes(...)` only owns dashboard, activity, feature-flag, and translation-style pages. It does not mount content-entry panel HTML, roles HTML, or settings HTML by itself.
- If navigation exposes `/admin/users`, `/admin/roles`, `/admin/profile`, or `/admin/settings`, verify the host also mounts the correct non-dashboard HTML owners such as `RegisterContentEntryUIRoutes(...)`, `RegisterRolesUIRoutes(...)`, `RegisterSettingsUIRoutes(...)`, or module-owned routes before treating the issue as dashboard work.
- If a host exposes canonical content-entry URLs such as `/admin/content/documents` or `/admin/content/agreements`, verify concrete canonical routes are registered before generic `/content/:name/*` handlers. Reversing that order can misroute `/new` and detail pages into the wrong handler.
- Register dashboard modules before `adm.Initialize(...)`.
- Register dashboard areas, providers, and renderer before `adm.Initialize(...)` when possible.
- Do not register a second dashboard HTML owner.
- Keep dashboard page presentation in `AdminPageChrome` and the shared layout
  enrichment boundary. Do not let widget providers own title, breadcrumbs,
  active navigation, the document, or arbitrary shell markup.
- Keep dashboard composition in setup or module code, not in domain services.
- Keep `Manifest()`, `Register(...)`, `RouteContract()`, and `MenuItems(...)` aligned.
- When a module-owned page reuses the shared sidebar template, verify the view context includes `nav_items`, `nav_utility_items`, `session_user`, and the intended active key. Missing utility nav is a shell-context bug, not a dashboard-placement bug.
- Feature-gate dashboard modules with `FeatureDashboard`.
- Route contracts declare relative UI routes. Menu items should target the path that matches that contract under the current admin base path.
- `Dashboard.RegisterProvider(...)` replaces any existing provider with the same code and removes previous default instances for that code.
- If an override provider omits `DefaultArea`, it intentionally prevents automatic default widget seeding. Use that pattern when replacing built-ins without duplicates.
- `DefaultConfig` is merged with persisted instance config at runtime.
- Use `admin.DecodeWidgetConfig[T](...)` for typed config. Unknown fields fail.
- Return `admin.WidgetPayloadOf(structOrPtr)` or `admin.EmptyWidgetPayload()`. Payload roots must be structs or pointers to structs.
- Keep payloads JSON-shaped. Do not return HTML fragments or legacy `chart_html` keys.
- Keep handlers thin: fetch data from stores or services, then project a canonical payload.
- Prefer `quickstart.WithDefaultDashboardRenderer(...)` or `quickstart.NewDashboardTemplateRenderer(...)` in quickstart-based hosts.
- If embedded templates are disabled, provide a template FS. Renderer construction fails otherwise.
- Custom renderers implement `admin.DashboardRenderer` and accept `admin.AdminDashboardPage`; the stock quickstart renderer rejects arbitrary map payloads.
- `quickstart.NormalizeDashboardTemplateData(...)` accepts a raw typed `dashboard.Page` only at the template-adapter compatibility boundary; it does not broaden the renderer interface.
- `quickstart.DashboardTemplatesFS()` returns `client.Templates()`. The compact quickstart dashboard document was removed and is not a fallback; caller filesystems are first-wins overlays on the canonical packaged stack.
- Use `quickstart.ResolveDashboardArea(...)` for shared main/sidebar/footer placement mapping.
- Use `RegisterArea(...)` for non-shared or scoped areas before registering providers that depend on them.
- Treat placement and area decisions as admin composition concerns.

## Task References

- Runtime, boot order, and route ownership: [references/runtime-lifecycle.md](references/runtime-lifecycle.md)
- Dashboard module, route contract, and menu wiring: [references/modules-and-navigation.md](references/modules-and-navigation.md)
- Provider registration, config decode, payload contract, and default widget behavior: [references/widgets-and-contracts.md](references/widgets-and-contracts.md)
- Renderer setup, template wiring, areas, placements, and layout checks: [references/rendering-and-placements.md](references/rendering-and-placements.md)

## Finish

- Route contract, menu target, and active nav key agree.
- If route shape changed, review `adm.RoutingReport()`, capture `adm.RoutingPlanner().Manifest()`, and use `routing.DiffManifests(...)` in tests or review.
- If sidebar or menu wiring changed, verify any menu-exposed non-dashboard pages still have HTML owners. Seeded links without mounted routes are a host wiring bug.
- Provider codes are stable and default widget seeding is intentional.
- Widget config decode and payload root stay typed.
- If widget contract or rendering changed, add contract tests and SSR or hydration regression coverage as needed.
- If dashboard-side browser writes changed, verify the cookie-backed browser path still satisfies CSRF for unsafe requests. Prefer package-managed helpers over widget-local token lookup.
- If dashboard-adjacent route ownership changed, verify the host did not reintroduce a custom browser-CSRF middleware path that diverges from `ProtectedBrowserRoute(...)`.
- Renderer or template changes still load the expected dashboard layout.
- Dashboard shell/component changes preserve typed page chrome, one
  shell/document owner, shared component CSS before namespaced product CSS,
  request-scoped theme data, and bounded sidebar/breadcrumb/footer overrides.
- If a dashboard template or shell override changed, verify `csrf_meta` still renders and any custom browser form includes `csrf_field`.
- If a module-owned page uses the shared sidebar partial, verify lower utility nav still renders and the shell matches quickstart-owned pages.
- Placement or area changes get a targeted assertion when practical.
- No duplicate dashboard HTML owner was introduced.
