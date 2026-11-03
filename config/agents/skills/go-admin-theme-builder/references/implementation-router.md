# Implementation ownership router

Use this reference after Figma intake and repository audit. Route each requested
change to one owner. A visual resemblance is not enough to move product
behavior into a theme package.

## Decision order

For each surface:

1. Identify the exact rendered primitive and its current owner.
2. Reuse that primitive and its supported theme, template, class, or asset
   seam.
3. If the seam cannot express a repeated semantic property, add one bounded
   additive consumer to the owning package.
4. Use a host override when the change is brand-specific or intentionally
   unique to one application.
5. Keep routes, permissions, state, data, commands, and workflows in the
   product module even when they are displayed by a themed primitive.
6. Record whether a runnable host, representative route, fixture/seed, and
   user/permission state exist. Without them, produce coverage/contract
   planning or use a disposable validation host; do not claim product runtime
   parity.

Do not create a parallel navigation, form, table, pagination, card, chart, or
empty-state system solely to match a design.

## Package decision table

| Question | Owner | Allowed work | Must not own |
|---|---|---|---|
| Does every renderer need deterministic safe token-to-CSS projection, portable profile validation, or generic diagnostics? | go-theme | additive renderer-agnostic types/helpers, variant-aware transport, safe normalization and serialization | markup, Tailwind classes, admin layout, chart policy, product semantics |
| Does the property affect form structure, controls, validation, actions, or form states? | go-formgen | semantic form consumers, fallback chains, partials, `ThemeConfig`, vanilla/Preact parity, default/minimal/unstyled preservation | admin navigation, dashboard charts, product submission behavior |
| Does it affect dashboard grids, widgets, metric cards, charts, legends, axes, tooltips, or chart palettes? | go-dashboard | dashboard-owned consumers and equivalent safe projection fixtures | hard go-theme dependency unless explicitly approved, product reporting queries |
| Does it affect admin shell, navigation, headers, shared cards/filters, DataGrid/table chrome, pagination, auth layout, or integration propagation? | go-admin | admin presentation consumers, typed primitive gaps, provider/context/static wiring | CRM routes, data, permissions, or public-site policy |
| Is it a logo, compact mark, favicon, font file, theme manifest, app-only template, or deliberate brand composition? | host theme | manifest values, source assets, supported filesystem/class overrides, build/mount configuration | copied framework internals or silent global palette remaps |
| Does it decide what records exist, who may act, where a link goes, or what a campaign/report does? | product module | routes, APIs, permissions, models, queries, actions, state, domain workflows | generic token transport or reusable renderer chrome |

If a change spans rows, split it into package-owned tasks with explicit
interfaces. Do not let the top-level screen name choose the owner.

## Primitive routing

| Design pattern | Reuse first | Bounded gap owner |
|---|---|---|
| Global/utility navigation | go-admin navigation registry and sidebar/header primitives | go-admin, only for reusable presentation or missing semantic state |
| Page title, pretitle, subtitle, breadcrumbs, active nav, body classes | go-admin `AdminPageChrome` and layout enrichment | go-admin |
| Trusted page actions | `page_header_actions` template block | go-admin for shared anatomy; host/product for action meaning |
| Card or stat card | existing admin/dashboard card or widget chrome | go-admin for general admin cards; go-dashboard for widget/metric semantics |
| Filters and search | existing filter controls plus form primitives | go-admin for DataGrid/filter composition; go-formgen for control rendering |
| Create/edit form | go-formgen renderer and admin panel/form adapter | go-formgen for reusable field/control chrome; product module for validation/actions |
| Data table | go-admin DataGrid/table primitive | go-admin for reusable table states and semantic consumers |
| Performance/reporting table | DataGrid when record-oriented; dashboard widget table when dashboard-owned | go-admin or go-dashboard according to the actual runtime primitive |
| Pagination | existing DataGrid/list pagination | go-admin |
| Empty/loading/error state | existing owning primitive state | the package that renders the state |
| Chart/funnel/time series | go-dashboard widget/provider/chart seam | go-dashboard for rendering; product module for data/query meaning |
| Brand image or UI icon | manifest asset role or owning package source asset | host for brand; owning renderer for a reusable UI icon slot |

Add a primitive only when all are true:

- at least two real consumers need the same semantic structure;
- no supported composition or override already expresses it;
- behavior and accessibility belong to the proposed package;
- the API can be additive and preserve current defaults;
- focused tests can prove legacy and themed behavior.

Otherwise compose existing primitives or keep the implementation host-local.

## Token and fallback routing

Portable tokens cover cross-renderer semantics. Component tokens remain in
package namespaces. Resolve:

```text
package/component token
  -> portable semantic token
  -> existing literal or class behavior
```

The last step is a compatibility fallback, not a new design value. go-theme
reports generic resolution/profile status; go-formgen, go-dashboard, and
go-admin report whether their own consumers consumed or ignored a supported
token.

Do not:

- replace broad Tailwind palette names globally;
- claim consumption because a token appears in a payload;
- move form or chart policy into go-theme;
- give go-dashboard a hard go-theme dependency merely to share fixtures;
- invent a literal when design authority is unavailable.

## Host override boundary

Use a host-owned manifest and source assets for brand values. Use
first-wins template filesystems only for intentional structural replacement.
Use class/renderer options where the owning package exposes them.

For shared browser presentation, consume the generated
`@goliatone/go-admin-client/components.css` export and add namespaced product
CSS afterward. Do not copy the canonical component stylesheet, import package
`src/` paths, or create a second modal/action-menu/status/filter vocabulary.

Promote a host override upstream only after it demonstrates a reusable gap.
When promoted, retain the host override as a compatibility fixture until the
new package contract is published and adopted.

Keep admin `theme` and public `site_theme` separate. A product may explicitly
share one selector, but that is host configuration, never an implicit admin
side effect.

## Coordinated local-development lane

For multi-package work:

1. Read each repository's `AGENTS.md` and `.ctx/README.md`.
2. Create or update the package-local feature context; never put sibling tasks
   in go-admin's manifest.
3. Use one disposable `go.work` outside all package repositories.
4. Add only the package modules required by the coordinated task and select the
   workspace explicitly with `GOWORK=/absolute/path/to/go.work`.
5. Run package tests from the owning repository and integration tests from the
   consuming repository.
6. Keep module `replace` directives and `go.work` files out of package diffs.
7. Remove the disposable workspace after local validation.

Local development does not wait for publication. Permanent dependency pins and
clean-host validation do wait for the user to publish reviewed versions. Do
not commit, tag, push, or publish packages unless the user explicitly requests
it.

## Review checks

Before implementation, confirm:

- every requested surface has one presentation owner and one product-behavior
  owner where applicable;
- runtime availability, representative routes, fixture/seed, and permission
  state are explicit rather than inferred;
- existing primitives were inspected before proposing new ones;
- host-only choices were not promoted into portable defaults;
- each new token names a real consumer and compatibility fallback;
- package-local context and tests exist for every sibling change;
- the temporary workspace is external and explicitly selected;
- no admin change implicitly modifies public-site theming.
