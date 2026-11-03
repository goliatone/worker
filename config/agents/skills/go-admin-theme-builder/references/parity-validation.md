# Parity validation

Use this workflow after intake and implementation to prove that an
authoritative design value reaches the rendered go-admin surface. A resolved
manifest token or generated bundle is an intermediate checkpoint, not parity.

## Contents

- Evidence gate
- Proof ladder
- Validation lanes
- Record the validation target
- Validate each layer
- Capture and computed-style procedure
- Representative surfaces and states
- Intentional divergences
- Planning-only validation
- Completion checklist

## Evidence gate

Start only with an exact design node and an approved source of values. Read
`figma-intake.md` when any node, variable, style, asset, mode, or maturity state
is unclear.

Classify the requested check:

- `runtime-parity`: exact node plus authoritative values, runnable route, and
  inspectable browser output exist;
- `contract-parity`: authoritative values and package consumers exist, but no
  runnable route is available;
- `coverage-only`: layout evidence supports primitive and ownership mapping,
  but exact values or runtime are unavailable;
- `blocked`: the exact node, authority, selected source, or target output
  cannot be inspected.

Never promote `coverage-only` or `contract-parity` to rendered parity. Never
sample a screenshot to fill a missing variable, mode, style, effect, or asset
value.

## Proof ladder

Prove every applicable layer in order:

1. **Design authority:** exact Figma node, variable/style/asset, source mode,
   state, dimensions, and authoritative value.
2. **Semantic mapping:** project meaning, portable or package-owned token,
   owner, constraint, fallback, and provenance record.
3. **Theme resolution:** manifest registration, requested theme/variant, base
   plus variant merge, reserved asset role, and resolved selection.
4. **Safe projection and package consumption:** projected variable or typed
   value, diagnostics, component-to-portable-to-current fallback, and a real
   go-formgen, go-dashboard, go-admin, or DataGrid consumer.
5. **Admin integration:** normalized `ThemeSelection`, request/preference
   precedence, payload propagation, template selection, and asset prefix/URL.
6. **Source-to-delivery chain:** source template/CSS/TypeScript/asset, owning
   build command, generated bundle or embedded filesystem, mount, HTTP
   response, and browser request.
7. **Rendered route:** actual host route, active variant, viewport, state,
   final DOM/asset, and computed values.
8. **Visual comparison:** geometry, typography, color, radius, shadow, asset
   shape, state presentation, and documented divergences against the exact
   source node.

For each failure, stop at the first unproved layer and route recovery to that
owner. Do not compensate at a later layer with broad host CSS.

## Validation lanes

Keep source-integration proof separate from released-module proof.

### Unpublished source lane

Use one temporary `go.work` outside all repositories and select it with an
explicit `GOWORK=/absolute/path/to/go.work`. Record:

- every workspace member and resolved module source;
- package revisions or other stable review identities;
- focused/full package tests and client build/tests;
- confirmation that no package `go.mod`, `go.work`, `replace`, or
  pseudo-version metadata was introduced.

Remove only the validated temporary directory after recording results. This
lane proves coordinated source behavior; it does not prove published
installability.

### Published module lane

Use `scripts/validate_go_module_artifact.sh module@version` for each exact
released module. Add `--require dependency@version` when the release depends on
a coordinated contract. The validator downloads into isolated caches, rejects
a main module or replacement, copies the downloaded artifact, and tests it
with `GOWORK=off` and `-mod=readonly`.

Record:

- exact go-admin, quickstart, go-theme, go-formgen, and go-dashboard versions;
- downloaded module path/version and confirmation that it was neither the main
  module nor a replacement;
- module graph and replacements;
- host module identity and Go/tool versions;
- focused/full package and client results;
- confirmation that the tested host does not resolve unpublished local source.

Use this lane for release reconciliation and disposable clean-host parity.
`GOWORK=off` inside a package checkout only proves that local source can build
without a workspace. Do not describe that, a local `replace`, or a repository
sibling as published-artifact proof.

## Record the validation target

Create or update a project-owned evidence record with:

| Field | Required evidence |
|---|---|
| Design source | exact node URL/name, verification state, source mode, variables/styles/assets, inspection date/tool |
| Runtime target | host/module identity, route, seed/fixture, user/permission state |
| Theme selection | requested/resolved theme and variant, selector inputs, preference/request overrides |
| Environment | package versions or source identities, Go/Node/browser versions, build identifier |
| Viewport | width, height, device scale factor, responsive state, scroll position |
| Surface/state | shell/list, detail/form, dashboard/chart, plus exact interaction state |
| Capture | screenshot path/reference and timestamp when runtime validation applies |
| Computed checks | selector, property, expected authoritative value, actual value, result |
| Contract checks | projection diagnostics, package consumer, template/asset source, HTTP result |
| Divergences | approved difference, owner, reason, evidence, expiry or follow-up |

Do not store credentials, session tokens, or bulky raw artifacts in the skill.
Keep live values and project identifiers in project context.

## Validate each layer

### 1. Design authority

- Open the exact frame/component/state node read-only.
- Confirm node name, dimensions, source mode, and verification state.
- Resolve the authoritative variable, style, effect, component property, or
  export setting for every property under comparison.
- Record base and active-mode values independently.
- Mark inaccessible library-owned values and exports as blocked.

### 2. Semantic mapping

- Trace the approved design source to a project semantic token.
- Trace that token to a portable or package-owned manifest key.
- Confirm owner, value constraint, runtime variable or typed value, consumer,
  and fallback chain.
- Reject mappings that skip semantic meaning or name no concrete consumer.

### 3. Selection and projection

- Assert manifest/registry identity and requested theme/variant.
- Assert base and variant merging without mutating the source manifest.
- Assert deterministic, safe projection and expected diagnostics.
- Distinguish `resolved`, `invalid`, `supported`, `unsupported`, `consumed`,
  and `unused`; only `consumed` proves renderer use.
- Assert canonical-over-alias behavior and invalid-value omission where
  relevant.

### 4. Package consumers

- go-formgen: verify package token, portable fallback, current default, chosen
  renderer/mode, and control/state markup.
- go-dashboard: verify rendered inventory, dashboard chrome, typed chart
  palette, concrete chart type, and named/custom theme composition.
- go-admin: verify semantic root, shell/shared primitive, auth/favicon, form
  adapter, DataGrid, and diagnostics as applicable.
- Confirm an absent aligned token preserves the package's prior default.

Run focused contract tests first, then the owning package's full suite.

### 5. Admin payload, templates, and assets

- Inspect the normalized admin theme payload at the route boundary.
- Confirm config, preference, request, provider, and final overlay precedence.
- Confirm the route uses the themed layout/context path.
- Resolve filesystem overrides by concrete first-wins template path.
- Treat manifest partial metadata only as renderer data.
- Resolve `logo`, `icon`, and `favicon` independently and verify expanded,
  collapsed, auth, and document-icon consumers.
- Verify asset prefix, mount, status, content type, final URL, and bytes.
- Assert admin `theme` changes do not leak into public `site_theme`.

### 6. Built and embedded output

- Identify the editable source file and owning build command.
- Rebuild through the package pipeline.
- Run generated-output contract tests.
- Confirm the served/embedded output contains the intended source change.
- Reject hand-edited `dist`, fingerprinted, generated CSS, or embedded output.

Passing this layer proves delivery integrity, not visual parity.

### 7. Rendered runtime

- Start the actual host using the recorded module lane and seed state.
- Navigate to the concrete route as the intended user/permission state.
- Select the target theme and active variant through supported inputs.
- Set the exact viewport before capture; record device scale and responsive
  breakpoint behavior.
- Wait for fonts, images, client hydration, DataGrid loads, and charts to
  settle. Record any deterministic wait condition.
- Inspect the final DOM, requested assets, console/network failures, and
  computed styles.

### 8. Visual comparison

Compare by surface and state, not by one full-page impression:

- frame geometry, content bounds, grid, gaps, alignment, and responsive flow;
- font file, family, style, weight, size, line height, and letter spacing;
- foreground, background, border, focus, status, and chart colors;
- control/surface size, radius, shadow layers, opacity, and motion-relevant
  presentation;
- logo/icon/favicon source, intrinsic geometry, view box, rendered size,
  aspect ratio, and optical alignment;
- hover, focus-visible, disabled, readonly, selected, loading, empty, error,
  permission, and active-variant output.

Use image comparison to locate differences, then confirm their cause through
DOM, computed style, layout geometry, and network/source evidence.

## Capture and computed-style procedure

For every capture:

1. Record route, fixture/seed, user/permission state, theme, variant, viewport,
   scale, browser, and build/module identity.
2. Reset nondeterministic UI: animations, clocks, random data, open menus,
   scroll, and focus unless the target state requires them.
3. Wait on an observable readiness condition, not an arbitrary delay.
4. Capture the full target frame and bounded component crops where details
   matter.
5. Inspect computed values on stable structural or data hooks.
6. Compare normalized units and colors while retaining the source units in the
   provenance record.
7. Repeat the default/base variant independently from the active variant.

A computed check should resemble:

```text
source: exact variable/style, mode, expected value
mapping: semantic token -> manifest key -> projected/typed value
consumer: package, source, stable selector
runtime: route, variant, viewport, state
actual: computed property or rendered asset geometry
result: pass, blocked, or divergence ID
```

Do not assert only that a CSS variable exists. Assert the final property that
the selected element or chart actually uses.

## Representative surfaces and states

Choose surfaces that exercise distinct owners:

| Surface | Minimum proof |
|---|---|
| Shell/list | layout, navigation/brand, header, filter, DataGrid/table, pagination, responsive behavior |
| Detail/form | form renderer/mode, labels/help/errors, controls, focus, disabled, readonly, loading, actions |
| Dashboard/chart | dashboard shell/cards/states, typed palette, series, legend, axis/grid/tooltip where the chart type renders them |
| Auth/admin brand | icon/logo/favicon precedence, URLs, intrinsic and rendered geometry |

Exercise only states defined by the design or required contract, but do not
skip a requested state because the default screenshot looks correct. Permission
and product behavior remain product-owned even when their presentation uses
themed primitives.

## Intentional divergences

Record a divergence only when the project accepts it. Include:

- stable ID and affected exact node/route/state;
- expected source and actual runtime value;
- owner and reason: product requirement, accessibility, browser/platform,
  framework limitation, or deliberate compatibility fallback;
- approval/evidence and whether the divergence is temporary;
- bounded upstream task or expiry condition when applicable.

Missing authority, missing consumers, stale bundles, and failed asset delivery
are blockers or defects, not intentional divergences.

## Planning-only validation

When a design is a wireframe, exact nodes are identified-only, token/style
authority is incomplete, or no host exists:

- validate page/surface coverage, viewport intent, primitive reuse, ownership,
  route/data dependencies, and state inventory;
- classify the maximum result as `coverage-only`;
- list every property and asset blocked on authority;
- do not create computed-style expectations, visual pass claims, or fallback
  literals;
- do not require a runnable product host merely to test routing quality.

The later clean-host test may prove the generic runtime contract with an
unrelated authoritative design. It does not retroactively prove parity for the
blocked wireframe.

## Completion checklist

- Exact source nodes and verification states are recorded.
- Every checked value has authority, semantic mapping, owner, constraint,
  fallback, and concrete consumer.
- Base/default and active variants are independently proven.
- Projection, diagnostics, package consumers, admin payload, templates,
  assets, and built delivery pass before visual review.
- The correct unpublished-source or published-module lane is recorded.
- Shell/list, detail/form, dashboard/chart, and applicable states are covered.
- Captures use the exact viewport and stable readiness conditions.
- Computed checks assert final properties, font/asset delivery, and chart
  presentation rather than token presence.
- Admin/public-site isolation remains intact.
- Divergences and blockers are explicit and project-owned.
- No missing value is guessed and no generated output is hand-edited.
