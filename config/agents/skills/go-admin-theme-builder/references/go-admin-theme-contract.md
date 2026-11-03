# Go-admin theme contract

Use this reference to map authoritative design values into a semantic theme
contract and then into consumers that actually render them.

## Contents

- Runtime selector and payload order
- Manifest, templates, and assets
- Consumer propagation
- Static delivery and source ownership
- Public-site isolation
- Current package seams
- Semantic mapping chain
- Token namespaces and ownership
- Value constraints
- Base and variant resolution
- Typography
- Spacing, sizing, radius, shadow, motion, and charts
- Brand and UI assets
- Source and generated ownership
- End-to-end examples
- Manual source discovery

## Runtime selector and payload order

The admin theme is one request-scoped selection. Follow the implementation in
`admin/admin.go`, `admin/theme.go`, and `admin/theme_adapter.go` in this order:

1. Start with `admin.Config.Theme` and `ThemeVariant`.
2. When preferences are enabled and a user ID is present, overlay the stored
   user theme and variant.
3. Overlay `ThemeSelectorFromContext`; route adapters populate that context
   from request inputs. Admin APIs accept `theme`/`variant` query values, with
   `X-Admin-Theme` and `X-Admin-Theme-Variant` as fallbacks where
   `selectorFromRequest` is used.
4. Seed the result from the constructor's default `ThemeSelection`.
5. Call the optional `ThemeProvider`. A non-nil successful selection merges
   name, variant, tokens, CSS variables, assets, partial metadata, chart theme,
   and asset prefix over the seed. `VariantResolved` lets a provider mark an
   empty variant and chart theme as authoritative.
6. Reconcile an attached manifest only when it matches the resolved theme.
   Retain declared named variants and clear unsupported variants to the base.
   On a provider error or nil selection, use the attached manifest base only
   when it represents the configured admin theme.
7. Apply final config overlays. `ThemeTokenOverrides`, `ThemeAssets`,
   `ThemeAssetPrefix`, `LogoURL`, and `FaviconURL` win for the fields they
   supply; legacy logo/favicon URLs win over same-key `ThemeAssets`.
8. Derive `ChartTheme` from the resolved variant when it is otherwise empty.

`ThemeSelection.Payload` returns cloned sections named `selection`, `tokens`,
`css_vars`, `assets`, `partials`, and `chart`. The asset prefix is transported
as `assets.prefix`. Consumers must tolerate absent sections.

Focused checks: `admin/theme_test.go`, `admin/preferences_test.go`,
`admin/admin_constructor_runtime_test.go`, and
`quickstart/auth_ui_routes_test.go`.

## Manifest, templates, and assets

`quickstart.NewThemeSelector` registers or reuses a `go-theme.Manifest`.
`WithThemeManifest` replaces the quickstart-generated manifest;
`WithThemeAssets` and `WithThemeVariants` fill generated defaults or missing
fields without overwriting a previously registered manifest. The default
manifest is compatibility behavior, not a portable semantic registry.

The generated quickstart manifest scopes its dark navigation surface through
`admin.sidebar.background`; it does not use the legacy `surface` alias for
that purpose. `surface` means `color.surface.default` and therefore affects
headers, controls, rows, and every other consumer of the portable default
surface. When a host supplies `surface` or `color.surface.default` explicitly,
do not add a component token that unintentionally shadows the host's portable
fallback. Use both tokens only when that precedence is deliberate.

The generated manifest declares both its `light` base label and `dark`
variant. A host base-only manifest instead leaves `Variants` empty and uses a
selector/provider that resolves `Variant == ""`. The go-theme adapters mark
that empty result authoritative. Preferences treats any non-nil manifest as
the option authority, so a base-only manifest advertises no named variants.

Within go-theme, resolution is:

- tokens: base map, then selected variant keys;
- templates: selected variant key, then base key, then the caller's fallback;
- assets: selected variant file and active prefix, then base file and base
  prefix;
- selector name: requested name, then configured default on registry failure;
- selector variant: requested variant, otherwise configured default.

The resolved selection name and manifest name must describe the same theme.
Older go-theme versions may load the default manifest while retaining a
missing requested name; cover the non-empty missing-name path before trusting
fallback identity in an adapter or cache key.

Reserve `logo`, `icon`, and `favicon` as separate asset roles. Quickstart fills
a missing `icon` from `logo`, but preserves an explicit icon. Admin config can
overlay resolved asset URLs after provider selection.

Manifest template entries are metadata. They only affect a renderer that reads
the corresponding key, such as go-formgen's `ThemeConfig.Partials` or
go-dashboard's `ThemeSelection.Templates`. They do not add files to the admin
view engine.

Admin template customization is instead a first-wins filesystem stack built by
`quickstart.WithViewTemplatesFS`: explicit overlays, host base templates, then
quickstart fallbacks. A file such as `partials/sidebar.html` overrides that
concrete path. Keep this separate from a manifest key such as `forms.input`.

Authenticated route presentation is a typed go-admin contract. Use
`AdminPageChrome` with `EnrichLayoutViewContextWithChrome`; non-zero typed
values win over legacy page keys. The type owns title, pretitle, subtitle,
breadcrumbs, active navigation, and body classes. It deliberately does not own
arbitrary HTML actions, which remain trusted `page_header_actions` template
content. A theme may select only the bounded sidebar, breadcrumbs, and footer
structural leaves; it must not add another shell or page-header owner.

Focused checks: `quickstart/theme_selector_test.go`,
`quickstart/view_engine_test.go`, go-theme `manifest_test.go`, and go-theme
`selector_test.go`.

## Consumer propagation

The resolved payload flows through typed boundaries rather than through a
global CSS rewrite:

| Consumer | Current seam | Evidence |
|---|---|---|
| Admin views/auth/navigation | `ThemePayload`, `WithThemeContext`, layout and nav context enrichment | `admin/theme_test.go`, `quickstart/auth_ui_routes_test.go`, `quickstart/nav_helpers_test.go` |
| Panel and settings forms | `PanelFormAdapter.ThemeResolver`, `SettingsFormAdapter.WithThemeResolver` | `admin/panel_form_adapter_test.go`, `admin/admin_test.go` |
| go-formgen | `render.ThemeConfig`; opt-in `orchestrator/defaults.WithThemeSelector`, `WithThemeProvider`, or `WithTheme` | go-formgen `pkg/orchestrator/defaults/defaults_test.go` and renderer contract tests |
| go-dashboard | structural `dashboard.ThemeProvider`; admin adapter copies tokens, templates, chart variant, assets, and prefix | `admin/dashboard_preferences_test.go`, go-dashboard `components/dashboard/theme_test.go` |
| CMS-backed admin screens | admin layout/panel/form context receives the same resolved payload | `admin/theme_test.go`, `admin/integration_test.go` |
| DataGrid and client primitives | admin view payload and source CSS/TypeScript; only explicitly consumed variables affect output | search source consumers and client tests before adding a token |

`WithAdminTheme` adapts a go-theme selector for the admin. It does not
automatically register form renderers, replace admin templates, mount assets,
or theme the public site.

## Static delivery and source ownership

`quickstart.NewStaticAssets` mounts distinct filesystem owners:

- admin assets at `<basePath>/assets`, ordered disk override, embedded host
  assets, extra fallbacks, then sidebar assets;
- go-formgen runtime and vanilla assets at `<basePath>/runtime` and
  `<basePath>/formgen` (including the compatibility `/runtime` alias);
- go-dashboard ECharts and shell assets at their package prefixes;
- sync-client assets through `RegisterSyncClientAssets`.

An asset URL in a manifest is not proof that bytes are mounted at that URL.
Verify the resolver/prefix, route registration, response, content type, and
final browser request. Use `quickstart/static_assets_test.go` and
`quickstart/view_engine_test.go` for precedence behavior.

Source assets, template/CSS/TypeScript entries, generated bundles, embedded
filesystems, and host mount configuration have different owners. Change source
and rebuild with the owning package's command. Do not edit generated bundles or
embedded output directly. In go-admin, inspect
`pkg/client/assets/package.json`, `input.css`, `vite.config.ts`, and `src/`
before changing client presentation; treat `dist/` and bundled `output.css` as
generated. The quickstart sidebar has its own source and embed boundary in
`quickstart/assets/` and `quickstart/sidebar_embed.go`.

Shared Admin modal, action-menu, status, filter, quick-filter, and button
presentation has one canonical source:
`pkg/client/assets/src/styles/components.css`. The embedded stylesheet imports
that entry, while public consumers import the generated
`@goliatone/go-admin-client/components.css` subpath. Package exports must point
only to `dist-public/`; a host must not import package `src/` paths. Mount
namespaced product CSS with `WithExtraAssetsFS` and load it after the shared
stylesheet through `head_extra`.

## Public-site isolation

Admin `theme` and public `site_theme` are separate contracts. Public routes use
`quickstart/site.SiteThemeProvider`, `SiteThemeSelector`, and an explicit
`WithSiteTheme`/`WithSiteThemeProvider` option. Site request overrides are
stored under their own context keys and projected into the richer
`site_theme` contract.

Never apply an admin theme selector to public delivery implicitly. A host may
explicitly pass the same go-theme selector to both systems, but isolation must
remain visible in configuration and tests. See
`quickstart/site/theme_provider.go`,
`quickstart/site/theme_integration_test.go`, and
`quickstart/site/context_resolution_runtime_test.go`.

## Current package seams

Use the active workspace, local, replaced, or cached source selected by the
audit helper:

| Package | Theme seam | Boundary |
|---|---|---|
| go-theme | `Manifest`, `Selector`, `Selection.Snapshot`, `RendererTheme` | renderer-agnostic transport, variant merge, asset/template resolution |
| go-formgen | `render.ThemeConfig` plus opt-in defaults resolver | owns form partials, classes, markup, and actual token consumption |
| go-dashboard | structural provider, selection, safe CSS-variable projection, chart/theme payload | owns dashboard widgets, charts, templates, and token consumption without a hard go-theme dependency |
| go-admin | provider adapter, preference/request precedence, context payload, view/static composition | owns admin chrome, DataGrid, integration wiring, and host override seams |

Do not assume the repository sibling is the compiled dependency. Record the
active `GOWORK`, workspace `use`/`replace` resolution, each module's `go`
directive, required version, module replacement, and resolved source. Treat
`github.com/goliatone/go-admin/quickstart` as a separate module even when it is
nested in a go-admin checkout. Search the selected source and its focused tests
for the named seam.

## Semantic mapping chain

Map in this order:

```text
exact Figma variable/style/asset
  -> project semantic token
  -> portable or package-owned manifest key
  -> approved CSS variable or typed renderer value
  -> concrete runtime consumer
  -> computed/rendered value under the active variant
```

Do not map a Figma primitive directly to an arbitrary CSS variable merely
because their values match. Name the product meaning first, then select the
portable or package owner. A successful manifest lookup is transport evidence,
not consumption evidence.

For each mapping retain:

- exact file/node and variable/style/asset ID;
- collection/library and source mode;
- source value and units;
- semantic token and owning package;
- manifest key, projected variable, and value constraint;
- component-specific fallback chain;
- consumer source/test;
- base and active-variant computed checks.

## Token namespaces and ownership

Use three levels:

1. Portable base tokens express renderer-independent UI semantics needed by
   more than one package.
2. Package extensions express component or surface semantics owned by
   go-formgen, go-dashboard, or go-admin.
3. Host tokens and asset values express brand-specific choices.

Keep go-theme renderer-agnostic. It can transport arbitrary tokens, enforce
generic safe projection, expose portable profile diagnostics, and serialize
deterministically. It must not define admin markup, form classes, chart policy,
or product-specific meanings.

Use package-owned names for component-specific behavior. Resolve them through:

```text
package/component token -> portable token -> current package default
```

The final default must preserve existing rendering when aligned tokens are
absent. Never globally remap broad Tailwind palette names to simulate semantic
consumption.

## Value constraints

Every token registry entry must declare one constraint:

| Kind | Allowed contract |
|---|---|
| Color | approved CSS color syntax; reject declarations, URLs, control characters, and unsafe delimiters |
| Length | finite number plus approved unit, or constrained zero; reject expressions unless explicitly owned |
| Number | finite bounded number for opacity, weight, ratio, or chart settings |
| Duration | non-negative finite time using approved units |
| Easing | approved keyword or validated cubic-bezier tuple |
| Font family | normalized family list; no declaration delimiters |
| Font weight | approved keyword or numeric range |
| Shadow | typed layers or strictly validated CSS shadow value |
| Identifier | normalized allowlisted token/variant/asset key |
| Asset path/URL | resolved through the theme asset contract, not emitted as an arbitrary CSS value |
| Chart palette | ordered, validated color list with deterministic partial fallback |

Use the shared projection safety contract for names, values, sorted map output,
and inline serialization. A package that intentionally avoids the shared
dependency must prove equivalent behavior through identical fixtures.

## Base and variant resolution

Treat each variant as a distinct resolution input:

1. record the Figma source mode for every mapped value;
2. define base manifest tokens and assets;
3. define only the variant overrides that differ;
4. resolve theme name and requested variant through the target selector;
5. confirm the resolved selection contains the expected merged values;
6. confirm the package supports and consumes each value;
7. inspect computed/rendered values with the active variant;
8. repeat the base/default case independently.

For a base-only theme, verify config defaults, stored preferences,
request/context previews, provider errors, the dashboard adapter, and
Preferences all finish with empty `Variant` and `ChartTheme`. Preserve the
legacy `default` sentinel only for applications without an attached manifest.

Do not infer that a correct base token proves a correct dark, high-contrast, or
brand variant. Do not use an unavailable variant value from another mode or
theme.

## Typography

Map typography as a group, not only a font family:

- family and fallback list;
- style/weight;
- size and unit;
- line height;
- letter spacing;
- text transform/decoration where semantic;
- paragraph spacing or measure when the consuming primitive owns it;
- source text style and source mode.

Prefer an authoritative Figma text style. If a visible text layer has raw
values but no declared style, record it as a local observation rather than a
portable token until the project approves that authority.

Verify the actual font is available to the client build and browser. A matching
CSS declaration with a substituted runtime font is not parity.

## Spacing, sizing, radius, shadow, motion, and charts

For spacing and size:

- preserve units and distinguish gap, padding, control height, icon size,
  sidebar width, content measure, and breakpoint semantics;
- map repeated primitives through semantic intent, not nearest numeric scale;
- keep layout values package-owned when they control one renderer.

For radius and shadow:

- record every corner or shadow layer needed by the source;
- use typed or validated values;
- verify state-specific and active-variant output;
- do not approximate an inaccessible effect style from a screenshot.

For motion-relevant presentation:

- map durations and easing only when Figma/prototype or another approved source
  is authoritative;
- keep interaction behavior in the owning renderer or product module;
- preserve the current behavior when aligned motion tokens are absent.

For charts:

- use an ordered semantic series palette plus status colors;
- keep chart theme/provider behavior in go-dashboard;
- define deterministic fallback for missing/partial palettes;
- verify legend, axis, grid, tooltip, series, and status presentation against
  their actual renderer consumers.

## Brand and UI assets

The admin brand roles are reserved:

| Role | Use |
|---|---|
| `logo` | expanded sidebar and full-brand contexts |
| `icon` | collapsed sidebar, compact brand contexts, and auth fallback where supported |
| `favicon` | document icon for admin and auth layouts |

Preserve each role independently. The host may intentionally reuse one file,
but absence normalization must not erase an explicit compact icon or favicon.
Verify expanded/collapsed sidebar behavior and auth/admin layout precedence.

Treat Figma UI icons as exported assets when the design supplies them:

- record the exact component/vector node;
- export with its frame bounds, view box, width/height, and aspect ratio;
- retain intended stroke/fill behavior and optical padding;
- do not reconstruct supplied icons with CSS or hand-drawn primitives;
- verify the asset in its final rendered slot, not only in isolation.

If no authoritative asset exists, record a gap. Do not promote a screenshot
crop, emoji, library lookalike, or existing host logo as the design source.

## Source and generated ownership

Identify:

- Figma/source export;
- normalized source asset committed to the host theme package;
- client source TypeScript/CSS/template entry;
- generated/bundled/embedded output;
- build command and contract tests.

Edit source assets and source client entries only. Rebuild generated bundles
through the owning package's normal pipeline. Never hand-edit embedded or
fingerprinted output to force parity.

Template manifest metadata and filesystem overrides are different mechanisms:

- manifest partial metadata is data consumed by a renderer that explicitly
  supports the key;
- first-wins template filesystems replace concrete template paths;
- a partial key does not create an override file, and an override file does not
  become manifest metadata.

## End-to-end examples

Use actual project tokens and source IDs. The names below illustrate the
required chain without supplying design values.

### Color

```text
Figma variable: semantic/surface/default, mode=Light
-> project token: surface.default
-> portable manifest key: color.surface.default
-> approved variable: --color-surface-default
-> consumer: shared card background
-> check: selected Light value equals computed background-color
```

Use the legacy `surface` alias only when compatibility with an existing
manifest requires it. A sidebar-only value maps to
`admin.sidebar.background`, not to the portable default surface.

### Spacing

```text
Figma variable: semantic/space/control-inline
-> project token: control.padding.inline
-> form package token -> portable space fallback -> current renderer default
-> consumer: vanilla and Preact control chrome
-> check: computed inline padding and responsive state
```

### Typography

```text
Figma text style: Body/Default
-> project token group: typography.body
-> manifest family/weight/size/line-height keys
-> consumer: shared form, table, and dashboard body text
-> check: loaded font plus computed family, weight, size, and line height
```

### Brand asset

```text
Figma logo component/vector
-> exported normalized source SVG
-> manifest asset role: logo
-> resolved theme asset URL
-> expanded sidebar <img>
-> check: final URL, intrinsic geometry, rendered dimensions, and aspect ratio
```

### UI icon

```text
Figma icon component
-> exported SVG with authoritative viewBox
-> owning package or host source asset
-> client build/embedded output
-> concrete button/navigation consumer
-> check: slot size, optical alignment, stroke/fill, and active state
```

If any Figma source above is missing, stop that chain at `design-source gap`;
never fill the next step with an invented literal.

## Manual source discovery

When the audit helper cannot run:

1. read the target `go.mod`, nested modules, and local `replace` directives;
2. resolve go-admin, go-theme, go-formgen, and go-dashboard from local sources
   or the existing module cache with network resolution disabled;
3. identify missing cached sources explicitly rather than downloading;
4. locate theme selectors/providers, manifest registration and variants,
   request/preference overrides, and payload adapters;
5. locate template filesystem composition, static/asset filesystem composition,
   client build entries, embedded output, and source assets;
6. search templates, CSS, TypeScript, and renderer code for actual token and
   CSS-variable consumers;
7. locate focused tests for every claimed contract;
8. keep admin `theme` separate from public-site `site_theme`.

The repository audit script prints a discovery index for these areas. Read the
sources and tests before implementation.
