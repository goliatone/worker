# Troubleshooting

Use this reference only after a concrete failure. Identify the first broken
layer, its owner, and its focused test before changing code. Do not recover by
guessing design values, broadening host CSS, editing generated output, or
changing module metadata speculatively.

## Contents

- Triage order
- Safety rules
- Design-source failures
- Theme selection and variant failures
- Projection and diagnostic failures
- Consumer and fallback failures
- Template, asset, and generated-output failures
- Module source, cache, workspace, and version failures
- Runtime and visual failures
- Failure simulations
- Recovery record

## Triage order

Check in this order and stop at the first failed contract:

1. exact Figma node and authoritative variable/style/asset;
2. semantic mapping, owner, constraint, and fallback;
3. manifest registration plus requested/resolved theme and variant;
4. safe projection and support diagnostics;
5. package-owned consumer and component fallback;
6. admin payload, template path, asset URL, and public/admin scope;
7. source build, generated bundle, embedded filesystem, and HTTP delivery;
8. host route, runtime state, computed value, and visual comparison.

Classify the owner as `design source`, `go-theme`, `go-formgen`,
`go-dashboard`, `go-admin`, `host theme/override`, `product module`, or
`environment/module graph`. A later layer must not mask an earlier failure.

## Safety rules

- Keep Figma read-only unless the user separately requests design edits.
- Never derive a missing token or asset value from a screenshot.
- Do not change manifests until selector identity and active variant are known.
- Do not pass invalid CSS values through a template safety escape.
- Do not add a package dependency, `replace`, pseudo-version, or repository
  `go.work` as an ad hoc repair.
- Do not delete or overwrite module caches; diagnose source resolution first.
- Do not edit `dist`, fingerprinted bundles, generated CSS, or embedded output.
- Do not apply admin `theme` fixes to public `site_theme`, or the reverse.
- Preserve current package defaults when aligned tokens are absent.
- After a fix, run the owning focused test before broader integration/parity.

## Design-source failures

### File or node cannot be inspected

Evidence:

- permission, plan limit, invalid node, unavailable library, or authenticated
  surface error;
- exact source URL and attempted node ID;
- whether metadata, screenshot, and export access fail independently.

Owner: design access/source.

Recovery:

1. Retry the exact node through one existing authenticated read-only surface.
2. Confirm the file key and branch key; do not invent alternatives.
3. Keep a layer-row ID `identified-only`.
4. Mark exact value/export work blocked and continue only coverage/ownership
   routing that the visible layout supports.

Do not request edit access, create a replacement design system, or promote a
visible pixel value to authority.

### Variables, styles, modes, or assets are missing

Evidence:

- exact property and affected node/state;
- local collection/style inventory and external-library ownership;
- whether the surface is wireframe, draft, or implementation-ready.

Owner: design source or project design authority.

Recovery: request the authoritative variable/style/export or an approved
project specification. Existing renderer defaults may preserve behavior but
must be recorded as defaults, not parity.

### Source mode does not match runtime variant

Symptom: values are internally consistent but compare against the wrong Figma
mode.

Owner: project mapping or host theme configuration.

Recovery: record source mode and runtime variant separately, inspect explicit
frame mode, then correct the project-owned mapping or selector input. Recheck
base and active variant independently.

## Theme selection and variant failures

### Requested theme resolves to another identity

Inspect:

- registry contents and configured default;
- requested name/variant from config, preference, request, and context;
- provider result/error and final config overlays;
- older dependency behavior for non-empty missing names.

Owner: go-theme selector, go-admin adapter, or host registration according to
the first wrong value.

Recovery: fix registration or precedence at the owning layer. Do not rename
the payload after resolution or override every token to imitate another theme.

### Base works but variant does not

Inspect:

- exact source mode and manifest variant key;
- requested and resolved variant;
- base/variant token and asset merge;
- variant-specific projected value and final computed property.

Owner: host manifest/mapping unless selection or merge is defective in
go-theme.

Recovery: correct only the wrong variant input/override. Do not copy a base
value into an unknown variant or treat base success as variant proof.

### Preference or request override appears ignored

Inspect the real precedence path:

```text
config -> preference -> request/context -> provider seed/result -> final config overlays
```

Owner: go-admin/quickstart integration or host configuration.

Recovery: test each input independently, remove accidental final overlays, and
verify the route uses the theme-aware context helper.

## Projection and diagnostic failures

### Token is `invalid`

Inspect token name, prefix, configured variable mapping, value constraint,
collisions, and stable diagnostic reason.

Owner: manifest value for bad input; go-theme only when valid input is rejected
contrary to the shared contract.

Recovery: correct the authoritative manifest mapping/value. Do not relax the
safety contract or emit the rejected value manually.

### Token is `unsupported`

Meaning: safe transport exists, but the target profile declares no semantic
support.

Owner: project mapping when the wrong token/profile was selected; package
renderer when a real reusable consumer is missing.

Recovery: map to an existing supported token, keep it host-owned, or propose a
bounded additive consumer in the narrowest renderer. Do not report it consumed
because the CSS variable exists.

### Token is supported but `unused`

Inspect the concrete rendered inventory, selected renderer/mode, chart type,
surface/state, and diagnostic consumer identifier.

Owner: package renderer or route composition.

Recovery: correct the real consumer/inventory or leave the diagnostic unused
when the surface is not rendered. Never force dummy markup or claim global
consumption.

### Diagnostics disagree with rendered output

Inspect component-token shadowing, portable fallback, invalid omission,
canonical-over-alias precedence, and the final element/chart inventory.

Owner: owning package consumer.

Recovery: make diagnostics use the same resolver and rendered inventory as the
output. Add a regression for both the consuming and shadowed token.

## Consumer and fallback failures

### Component token does not win

Expected:

```text
component/package token -> portable token -> current package default
```

Inspect projected names, resolver order, explicit classes/partials, and whether
the component exists in the selected renderer mode.

Owner: go-formgen, go-dashboard, or go-admin/DataGrid.

Recovery: fix the package resolver or stable structural/data hook. Do not
globally remap Tailwind palette names.

### Portable fallback does not apply

Inspect whether the component token is truly absent, the portable value is
valid/supported, and the package maps that portable key for the actual state.

Owner: package renderer.

Recovery: repair the bounded fallback map and cover component override,
portable fallback, invalid input, and current-default cases together.

### Empty/legacy theme changes appearance

Owner: package that introduced an unconditional declaration/class/markup
change.

Recovery: make semantic output opt-in, restore the prior literal/class as final
fallback, and rerun legacy/empty fixtures. Do not encode the new appearance as
the compatibility default.

### Form, chart, or DataGrid is unaffected

Inspect the actual renderer:

- form renderer, style mode, partial/class override, and state hook;
- dashboard inventory, chart type, named/custom theme, palette cache identity;
- DataGrid runtime structure, stable semantic classes/data hooks, and selected
  state.

Owner: the package that renders the unaffected primitive, not go-theme.

Recovery: use or add one bounded package consumer. Host-specific glue is not a
substitute for a shared missing consumer.

## Template, asset, and generated-output failures

### Template override is ignored

Inspect concrete template path, first-wins filesystem order, host base/fallback
stack, and the view engine used by the route.

Owner: host override configuration or quickstart view-engine composition.

Recovery: place the file at the exact supported path and fix filesystem order.
Do not add a manifest partial key; partial metadata does not replace files.

### Manifest partial has no visual effect

Inspect whether the selected renderer reads that exact partial key.

Owner: renderer integration or incorrect project assumption.

Recovery: use a supported renderer partial key or a concrete filesystem
override. Do not create dynamic admin includes merely to make metadata appear
active.

### Logo, icon, or favicon is missing/wrong

Inspect each reserved role independently:

- manifest/base/variant asset and final config/legacy override;
- asset prefix and resolved URL;
- expanded, collapsed, auth, or document-head consumer;
- mount, status, content type, bytes, SVG view box, intrinsic geometry, and
  rendered aspect ratio.

Owner: host manifest/source asset, quickstart static delivery, or go-admin
layout consumer according to the first failure.

Recovery: fix that role or delivery seam. Do not replace a supplied icon with
CSS, copy generated output, or silently reuse another role over an explicit
asset.

### Source changed but browser output is stale

Inspect build entry, build timestamp/hash, generated contract tests, embed
source, mounted filesystem order, HTTP cache, and browser network response.

Owner: owning package build/delivery pipeline.

Recovery:

1. rebuild from source with the package command;
2. verify generated/embedded output and served bytes;
3. restart the host when embed output is compiled into the binary;
4. clear only bounded application/browser caches when evidence identifies
   them.

Never patch the generated bundle or delete unrelated caches.

## Module source, cache, workspace, and version failures

### Audit reports a missing module source

Inspect active `GOWORK`, target/nested `go.mod`, `replace` directives, module
cache entry, `GOMODCACHE`, and exact required version with network disabled.

Owner: environment/module graph.

Recovery: report the missing cached source. Do not download during the
read-only audit or populate its isolated cache. A later authorized build may
resolve modules normally.

### Wrong source tree is inspected or compiled

Inspect:

```sh
go env GOWORK GOMOD GOMODCACHE
go list -m -json <module>
go work edit -json   # only for the explicitly selected workspace
```

Owner: environment/workspace selection.

Recovery: select the intended external workspace with an absolute `GOWORK`.
For standalone local-source proof, set `GOWORK=off`. For published-artifact
proof, use `scripts/validate_go_module_artifact.sh module@version` and confirm
the reported source is the isolated module cache. Do not infer source from a
nearby repository directory.

### Workspace test passes but standalone build fails

Likely cause: a package `go.mod` still pins a release that lacks APIs supplied
by the workspace.

Owner: package release metadata/handoff.

Recovery: confirm the required release exists and is user-approved, update the
direct dependency pin, run the package with `GOWORK=off`, then validate the
exact release with `scripts/validate_go_module_artifact.sh` and the required
dependency coordinate. Do not leave a workspace, replacement, or
pseudo-version as the permanent repair.

### Local standalone tests pass but the released module fails

Likely cause: the release tag omitted a tracked fixture/generated file, or the
published `go.mod` differs from the locally selected dependency graph.

Owner: package release pipeline.

Recovery: validate the exact downloaded coordinate with
`scripts/validate_go_module_artifact.sh`, fix the tracked source or dependency
pin, and add a release preflight that tests `git archive HEAD` with
`GOWORK=off` and `-mod=readonly` before tagging. Publish a corrective version;
do not treat the local checkout or module-cache edits as a repair.

### Package versions are skewed

Inspect the dependency matrix, published versions, public API availability,
fixture version/hash, Go baselines, and renderer optional-dependency boundary.

Owner: release coordination or the direct consumer module.

Recovery: use the documented compatible set in dependency order. Preserve
go-dashboard's optional theme boundary unless an approved design changes it.
Do not upgrade unrelated dependencies during the repair.

### Explicit `GOWORK` path is missing or wrong

Owner: environment/workspace selection.

Recovery: fail closed, recreate one disposable workspace outside package
repositories from known absolute paths, verify `go env GOWORK` equals that
file, and list members before testing. Remove only the validated temporary
directory afterward.

## Runtime and visual failures

### Admin theme appears on public routes, or `site_theme` appears in admin

Inspect selector/provider registration, request context keys, route group,
layout payload key, and isolation tests.

Owner: quickstart/host wiring.

Recovery: restore explicit separate providers/contexts. Sharing a selector must
remain an explicit host option; never patch public templates with admin
variables as recovery.

### Payload is correct but computed value is wrong

Inspect package consumption, selector specificity, explicit class/partial
overrides, stale bundle delivery, active variant, browser font/asset load, and
final computed property.

Owner: first layer that diverges after payload propagation.

Recovery: fix the stable consumer or supported override. Do not stop at
variable presence or add `!important` globally.

### Screenshot differs but computed values match

Inspect font substitution, intrinsic asset geometry, layout bounds, content
fixtures, browser/scale, responsive breakpoint, chart animation/data, and
interaction state.

Owner: host fixture/environment, source asset, package layout, or product data
according to evidence.

Recovery: normalize the recorded runtime conditions or fix the owning geometry.
Do not change tokens merely to make one nondeterministic capture closer.

## Failure simulations

Use these checks when validating this reference:

| Simulation | First failed layer | Owner | Safe recovery |
|---|---|---|---|
| Exact design node opens, but local variables and library styles are unavailable | design authority | design source | mark exact values blocked; continue coverage only |
| Active variant contains `color.action.primary: url(...)` and projection reports invalid | projection | host manifest value | correct from authoritative variant source; keep unsafe value omitted |
| Host adds a manifest `partials.sidebar` key but the admin sidebar remains unchanged | template mechanism | host override | use the exact first-wins `partials/sidebar.html` path |
| External workspace passes, but `GOWORK=off` consumer build lacks a new API | module graph/version | direct consumer module | pin the published approved dependency and rerun standalone |
| Admin route is correct, but public route receives the admin token payload | runtime scope | quickstart/host wiring | restore separate admin/site contexts and isolation tests |

Each simulation must end at the owning source and focused contract test before
broader parity.

## Recovery record

Record:

- symptom, route/node/state, and first failing layer;
- active theme/variant and module lane;
- expected versus actual source, payload, delivery, and computed evidence;
- owner and bounded fix;
- focused test plus broader validation result;
- remaining blocker or divergence ID.

If ownership or authority remains ambiguous after three review/fix cycles, stop
and report the unresolved high/medium issue instead of stacking speculative
repairs.
