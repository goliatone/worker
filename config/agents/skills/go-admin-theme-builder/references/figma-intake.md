# Figma intake and coverage

Use this workflow before extracting theme values or planning implementation.
Keep Figma read-only unless the user separately asks to change the design.

## Intake contract

Require a Figma Design URL in this form:

```text
https://www.figma.com/design/<file-key>/<file-name>?node-id=<page-or-node-id>
```

Use the branch key when the URL targets a branch. Reject file-only links for
value extraction: ask for or discover an exact page, section, frame, component,
or component-set node. Normalize `node-id=123-456` to API ID `123:456` without
changing the source URL recorded in project context.

For every intake, record:

- source URL, file key, node ID, node name, and page name;
- verification state for each node: `semantic-verified`, `visual-verified`,
  `identified-only`, or `blocked`, plus the evidence that earned that state;
- access mode and whether semantic metadata, screenshots, and exports work;
- inspection date and the tool or visible authenticated surface used;
- requested viewport, variant/mode, and implementation request;
- target repository/context location for live coverage state.

Do not store share tokens, session parameters, credentials, or sensitive raw
artifacts.

Use the verification states as mutually exclusive evidence levels:

- `semantic-verified`: an exact-node semantic API/connector response confirms
  node identity and inspectable metadata;
- `visual-verified`: an isolated exact-node render or screenshot confirms node
  identity and visual scope, but semantic values remain unverified;
- `identified-only`: the supplied URL, a stable browser property panel, or a
  matching layer row identifies the candidate without exact semantic or
  isolated-render evidence;
- `blocked`: no authorized surface can confirm the exact node.

Record the strongest state actually earned. Browser structure or dimensions do
not earn `semantic-verified`, and a stable property panel without an isolated
render remains `identified-only`. A screenshot of the surrounding Figma
browser UI is not an isolated exact-node render and does not earn
`visual-verified`.

## Read-only access preflight

1. Open or query the exact node without requesting edit access.
2. Confirm the file and node names match the request.
3. Enumerate top-level pages before concluding assets or components are absent.
4. Query the exact node metadata and, when useful, a screenshot.
5. Inspect local variables, modes, text styles, paint styles, effect styles,
   grid styles, components, component sets, instances, and available libraries.
6. If a tool rejects the file or exact node, record the error category and try
   one existing authenticated read-only surface. Do not guess alternate file
   keys or node IDs.
7. If no authorized surface can inspect the node, stop value extraction and
   report an access blocker. Screen names supplied by the user may inform
   coverage, but they do not become authoritative values.

An ID copied from a visible layer row is `identified-only`. Do not call the
node inspected or verified until the exact node URL, semantic API, or isolated
node render confirms the node name and scope. Record rate limits, permission
failures, invalid-node failures, and unavailable-library failures per attempted
node rather than promoting a batch of candidates to verified status.

Never request a Figma seat, edit permission, library publication, or mutation
as an automatic recovery step.

### Plan limits and browser fallback

When the semantic connector reports a seat, plan, quota, or tool-call limit:

1. stop repeated connector retries after the exact blocker is recorded;
2. open the exact supplied URL in one existing authenticated browser surface;
3. confirm the file, selected node name/type, and dimensions only when the
   selection and property panel remain stable;
4. use an isolated exact-node render or screenshot only to earn
   `visual-verified`, never semantic value authority;
5. keep matching layer-list rows `identified-only` when selection properties
   do not stabilize;
6. record whether variables, styles, modes, libraries, and exports remain
   unavailable, then continue coverage/ownership planning only.

A browser fallback can verify exact structure and viewport dimensions. It
cannot promote colors, typography, spacing, effects, modes, or asset exports
without stable authoritative properties.

## Inventory

Build a bounded inventory for the requested scope.

### Pages and sections

- page names and IDs;
- top-level sections/frames and exact node URLs;
- frame dimensions and intended viewport;
- repeated screens, archived iterations, and improvement pages;
- comments or annotations that materially change maturity or scope.

### Components and libraries

- local components and component sets;
- instance/library ownership and variant properties;
- shared navigation, header, card, filter, form, table, pagination,
  empty/loading/error, dashboard, and chart patterns;
- detached or one-off frames that only resemble reusable components.

Do not treat an instance's visible value as a local design token when its
authority belongs to an inaccessible external library.

### Variables, modes, and styles

- local collections, variable names/types/scopes, aliases, and modes;
- applied explicit modes on representative frames;
- local and library text, paint, effect, and grid styles;
- raw unstyled values that repeat but have no declared authority;
- which source is authoritative for color, typography, spacing, sizing,
  radius, shadow, icon geometry, motion, and chart presentation.

### Exportable assets

- logo, compact icon, favicon, UI icons, illustrations, and raster imagery;
- source node/component ID, export format/scale, frame bounds, view box, and
  aspect ratio;
- whether the asset is local, library-owned, or unavailable;
- intended source path versus generated/built output path.

## Design maturity

Classify each requested surface independently:

| State | Evidence | Implementation consequence |
|---|---|---|
| Exploratory | sketches, alternatives, comments, incomplete structure | coverage only; do not freeze values |
| Wireframe | stable information architecture but incomplete styles/tokens | route primitives and product ownership; exact parity is blocked |
| Visual draft | concrete values exist but components/modes are inconsistent | map only values with identified authority; record gaps |
| Implementation-ready | exact node, authoritative variables/styles/assets, modes, and states exist | semantic mapping and parity may proceed |
| External-library-owned | instances reference a library not available to the inspector | request library authority or record a blocker |

A file can be implementation-ready for layout coverage and still be a
wireframe for token authority.

## Coverage mapping

Keep live, project-specific coverage in the target repository's canonical
context. Use bounded evidence only when the target project does not exist.
Create one row per relevant surface:

| Field | Required value |
|---|---|
| Figma source | exact node URL and name |
| Node verification | semantic-verified, visual-verified, identified-only, or blocked |
| Surface/state | screen, component, or interaction state |
| Existing primitive | concrete go-admin, go-formgen, or go-dashboard primitive |
| Ownership | go-theme, renderer package, go-admin, host override, or product module |
| Route/data dependency | route, permissions, API/data, or `none` |
| Design authority | variables/styles/assets source or explicit gap |
| Validation | blocked, inventoried, mapped, implemented, or parity-verified |
| Notes | bounded divergence or upstream gap |

Separate:

- screen/layout coverage from token/style authority;
- reusable presentation from domain routes, data, permissions, and behavior;
- existing primitives from missing reusable consumers;
- implemented output from parity-verified output.

## Missing authority

When an authoritative value is missing or inaccessible:

1. name the property and affected nodes/states;
2. name the missing authority: local variable, mode, style, library, export,
   or approved specification;
3. mark the coverage row `blocked` for exact value/parity work;
4. continue ownership and primitive routing when layout evidence is sufficient;
5. do not sample screenshots, average pixels, inherit an unrelated project
   token, or introduce a fallback literal and call it parity.

Defaults may preserve an existing host's rendering, but they are not evidence
of the requested design value.

## Provenance ledger

Before mapping values into a manifest, create or update a project-owned ledger
with one row per semantic property:

| Field | Meaning |
|---|---|
| Semantic token | project meaning, independent of source or renderer |
| Figma authority | exact variable/style/asset node and collection/library |
| Source mode | exact Figma mode and resolved value |
| Manifest key | base or package-owned token key |
| Runtime variable | approved CSS custom property, when applicable |
| Consumer | concrete template, renderer, chart, or client source |
| Owner | go-theme, package renderer, go-admin, or host |
| Constraint | allowed type/format/range |
| Fallback | component token, portable token, then existing default |
| Validation | source value, selected variant, and computed runtime value |

Keep source mode and runtime variant explicit. Record base and active variant
values as separate checks; never overwrite provenance with the final CSS
literal alone.

## Handoff

Before implementation, produce:

- the exact-node inventory and maturity classification;
- the coverage mapping;
- authoritative variable/style/asset sources;
- explicit design-source and access gaps;
- product-owned routes/data/behavior excluded from theme work;
- the smallest relevant next reference:
  `go-admin-theme-contract.md` for runtime mapping or
  `implementation-router.md` for ownership decisions.
