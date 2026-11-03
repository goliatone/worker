---
name: go-admin-theme-builder
description: Build or review source-grounded custom go-admin themes from Figma designs. Use for Figma-to-go-admin translation, admin theme manifests and variants, semantic token and CSS-variable work, logo/icon/favicon assets, admin template customization, renderer ownership across go-theme/go-formgen/go-dashboard/go-admin, and rendered visual parity reviews.
---

# Go Admin Theme Builder

Build from authoritative design values through the runtime consumers that
actually render them. Do not treat a resolved manifest token as proof of visual
support.

## Preflight

1. Read the target repository's `AGENTS.md` and equivalent local guidance.
2. If `.ctx/` exists, read `.ctx/README.md` and the relevant requirements,
   design, and tasks before meaningful feature work. Use that context rather
   than creating ad hoc planning files. If the user explicitly restricts
   context-document access for an evaluation or review, honor that narrower
   scope, record the resulting limitation, and do not infer hidden context.
3. Locate the target module, active go-admin/quickstart wiring, go-theme
   manifest and selector, go-formgen and go-dashboard integrations, template
   filesystems, static assets, and client build sources. Do not assume paths
   from this repository.
4. Read the owning source and focused tests before proposing or making changes.
5. Keep the admin `theme` contract separate from the public-site `site_theme`
   contract.
6. For Admin shell or shared-component work, read
   `docs/GUIDE_VIEW_CUSTOMIZATION.md`, `docs/GUIDE_UI_PRIMITIVES.md`,
   `docs/GUIDE_THEME.md`, and `docs/GUIDE_FRONTEND.md` from the selected
   go-admin source before changing a host override.

Run `scripts/audit_go_admin_theme.sh <repository-root>` when a POSIX shell is
available. It is a read-only discovery index, not a substitute for source
inspection. Use the manual route in
[go-admin-theme-contract.md](references/go-admin-theme-contract.md) otherwise.

## Route the operation

- For Figma access, exact-node intake, design maturity, source authority,
  variables/styles, export inventory, and coverage mapping, read
  [figma-intake.md](references/figma-intake.md).
- For selectors, manifests, tokens, variants, brand roles, template and asset
  delivery, package seams, and manual source discovery, read
  [go-admin-theme-contract.md](references/go-admin-theme-contract.md).
- For deciding whether work belongs in go-theme, go-formgen, go-dashboard,
  go-admin/DataGrid, a host override, or a product module, read
  [implementation-router.md](references/implementation-router.md).
- For end-to-end rendered comparison, active-variant computed values, viewport
  capture, interaction states, and intentional divergences, read
  [parity-validation.md](references/parity-validation.md).
- For missing authority, invalid or unused tokens, precedence, module-cache,
  workspace, generated-asset, or runtime failures, read
  [troubleshooting.md](references/troubleshooting.md).

Load only the references needed for the current operation. All references are
one level below this file.

## Ownership boundary

Route every change to the narrowest owner:

1. `go-theme`: renderer-agnostic selection, manifest transport, safe generic
   projection, portable profile support, and shared diagnostics.
2. `go-formgen` or `go-dashboard`: package-specific semantic consumers and
   rendering states.
3. `go-admin`: admin payload adapters, shell/shared primitives, safe layout
   projection, typed page chrome, favicon rendering, and embedded/public
   DataGrid and client-component presentation.
4. Host theme/override: brand values and assets, manifest configuration, and
   supported first-wins template or asset overrides.
5. Product module: routes, permissions, data, workflows, and domain behavior.

Do not hide a reusable framework gap behind broad host CSS. Document the gap
and make a bounded upstream change with contract tests.

Keep manifest metadata, template filesystem overlays, SSR primitives, browser
components, and product CSS as separate delivery tiers. New authenticated
routes use `AdminPageChrome` plus `EnrichLayoutViewContextWithChrome`; trusted
action markup remains template-owned. Shared modal/action-menu/status/filter/
quick-filter/button styling comes from the canonical go-admin component source
and the generated `@goliatone/go-admin-client/components.css` export. Never
copy that source into a theme package or import package `src/` paths.

## Cross-package development

Before editing a related repository, read its local guidance and context.
Create or update package-local `.ctx` context when that repository already uses
it; do not add sibling spec IDs to the go-admin manifest.

Develop coordinated local sources through one temporary `go.work` outside the
package repositories and select it explicitly with `GOWORK`. Never add
package-local workspaces, permanent `replace` directives, or unpublished
pseudo-versions. Continue local package work without waiting for manual
publication. Permanent version pins and the final clean-host proof must use
versions the user reviewed and published.

For released-module proof, run
`scripts/validate_go_module_artifact.sh module@version` (and `--require
dependency@version` for coordinated contracts). This downloads and tests the
exact module artifact in isolated caches. `GOWORK=off` in a local checkout is
standalone-source evidence, not published-artifact evidence.

Do not commit, tag, push, or publish package changes unless the user explicitly
requests that action.
