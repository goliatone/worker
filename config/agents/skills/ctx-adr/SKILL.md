---
name: ctx-adr
description: Create, review, revisit, relate or supersede project ADRs through ctx adr; use for architectural decisions in repositories using .ctx before or alongside feature planning.
---

# Project ADR lifecycle

Write authored documents as the responsible developer or project team. State requirements and rationale directly; “user” means the feature's end user, not the requester in the conversation. Apply the ctx skill's Document voice rules, including review of conversation-dependent wording and preservation of attribution, decision status and source evidence.

Read `.ctx/README.md` and the project ctx workflow. ADRs are optional; a spec/task or TDD may proceed without one. Significant choices may warrant a recommendation, not an automatic capture or approval gate. Ordinary planning can retain unresolved choices in DESIGN.

When ADR management is explicitly authorized, search existing records before creating one. Preserve decision identity and accepted status. Draft capture neither accepts a recommendation nor authorizes implementation. Use guarded lifecycle commands for acceptance or supersession only with authorized human intent. Link adopted decisions from DESIGN; review-only work reports issues without mutation.

Use `ctx adr list`, `search`, `show` and `validate` to inspect canonical records. `show --json` includes the current opaque revision; plain show returns Markdown. Mutate through `ctx adr` commands; do not bypass their write guards by editing canonical files directly.

- `ctx adr create "Decision question" --body-file body.md` creates draft/deferred work. Body files contain Markdown without front matter; `-` reads stdin.
- `ctx adr status ADR-0001 --status proposed --revision <revision>` proposes a draft. A proposal can become accepted or rejected; either closes its current work.
- `ctx adr revise ADR-0001 --body-file body.md --revision <revision>` revises text. Accepted clarification requires `--reason` and must preserve the Decision section.
- `ctx adr revisit ADR-0001 --reason "New evidence" --revision <revision>` queues accepted work in Backlog while retaining acceptance. `--state todo` or `doing` selects another open state.
- `ctx adr relate ADR-0001 --kind spec --target feature-id --revision <revision>` links known specs, epics or ADRs. `--remove` removes that relation.
- A reversal requires a new accepted ADR, then `ctx adr supersede ADR-0001 --target ADR-0002 --revision <old-revision> --replacement-revision <new-revision>`.

Retain the same `--idempotency-key` and payload when retrying an uncertain write. Reload after stale revision errors; do not silently overwrite. `ctx adr move` changes work independently from the decision; closed accepted work reopens through revisit.

Legacy support ADRs are qualified by spec and filename. `ctx adr adopt --preview` lists candidates; preview one candidate, then adopt it explicitly with `--preview-revision`. Originals remain untouched and copied relative links need review.

`ctx prompt adr create`, `review ADR-0001`, `revisit ADR-0001`, and `create-spec ADR-0001` render current context. Rendering never performs the action. A create-spec prompt does not create or approve a spec. Workbench exposes guarded ADR forms and Work cards; start it with `--write` to enable mutations.

Use the core ctx skill for task and project-policy guidance and executable resolution. Install the ctx skill family using `ctx setup skills install`; use `ctx setup skill skills/ctx-adr/SKILL.md` for this package alone.
