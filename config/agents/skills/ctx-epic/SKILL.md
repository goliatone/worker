---
name: ctx-epic
description: Manage epic documents and epic-linked specs in repositories that use .ctx. Use this skill to create epics, create child specs under an epic, review epic coverage, align specs with epic goals, and resolve epic-level open questions.
---

# ctx-epic skill

## Purpose

Use this skill for initiative-level `.ctx` workflows.

Epics are optional grouping documents. They give related specs shared context without changing the flat `.ctx/specs/<feature>/` layout.

Expected layout:

```text
.ctx/
  README.md
  epics/
    <epic>/
      README.md
  specs/
    <feature>/
      REQUIREMENTS.md
      DESIGN.md
      TASKS.md
      REVIEWS.md
```

## Core rules

Write authored documents as the responsible developer or project team. State requirements and rationale directly; “user” means the feature's end user, not the requester in the conversation. Apply the ctx skill's Document voice rules, including review of conversation-dependent wording and preservation of attribution, decision status and source evidence.

- Epic support is optional.
- Specs remain under `.ctx/specs/`; do not nest specs under `.ctx/epics/`.
- `epic:` front matter in `.ctx/specs/<feature>/REQUIREMENTS.md` is the source of truth for membership.
- Missing `epic:` means the spec is standalone.
- `.ctx/epics/<epic>/README.md` is contextual documentation, not the authoritative child list.
- The epic progress tracker in `.ctx/epics/<epic>/README.md` is generated context, not a source of truth.
- Canonical progress state lives in `.ctx/manifest.json`, child `epic:` front matter, and child `TASKS.md`.
- `<epic>-<spec>` is the default naming convention for new child specs only.
- Existing specs attached to an epic keep their current slug unless the user explicitly requests `--rename`.
- Filename prefixes are not the source of truth for membership.
- Keep epic docs lighter than full feature specs.
- Keep child specs readable as standalone docs.
- Do not create ad hoc planning files. Explicitly authorized canonical ADRs, review records and handoffs follow the core ctx workflow.

## Helper resolution

Use the core ctx skill's helper resolution: executable `CTX_CLI_BIN`, repository-local `./ctx`, then `ctx` on PATH. The `ctx.sh` compatibility launcher translates legacy names and requires the same native binary. Use the native command surface below.

## When to use this skill

Use this skill when the user asks to:

- create an epic
- create a child spec under an epic
- attach an existing spec to an epic
- detach a spec from an epic
- review an epic and its child specs
- align child specs with epic goals
- resolve epic-level open questions or cross-spec decisions

Use the core `ctx` skill alongside this skill for task capture, project policy, Git ownership, reviews and handoffs, including epic-only material work. Epic-only reviews and handoffs use the selected feature task home, normally `project-operations`. Orchestrated children leave commits, shared-state updates and handoff persistence to the parent.

## Mode 1. Create Epic

Use this mode when creating `.ctx/epics/<epic>/README.md`.

Steps:

1. Read `.ctx/README.md` if it exists.
2. Normalize the epic name to kebab case.
3. Prefer `ctx epic new <epic>` when available.
4. Create `.ctx/epics/<epic>/README.md` if missing.
5. Keep the document lightweight:
   - Summary
   - Goals
   - Non Goals
   - Child Specs
   - Ordering and Dependencies
   - Open Questions
6. Do not create `REQUIREMENTS.md`, `DESIGN.md`, or `TASKS.md` for the epic unless explicitly asked.

## Mode 2. Create Child Spec

Use this mode when creating a new spec linked to an epic.

Steps:

1. Read the core `ctx` skill.
2. Read `.ctx/README.md`.
3. Read `.ctx/epics/<epic>/README.md` when it exists.
4. Prefer `ctx spec new <spec> --epic <epic>` when available.
5. Default the new spec slug to `<epic>-<spec>`.
6. Do not double-prefix when the requested spec already starts with `<epic>-`.
7. Create or update the normal child spec docs:
   - `REQUIREMENTS.md`
   - `DESIGN.md`
   - `TASKS.md`
8. Set `epic: <epic>` in canonical `REQUIREMENTS.md` front matter.
9. Keep the child spec aligned with the epic while preserving clear standalone behavior, design, and tasks.
10. Update `.ctx/manifest.json` through `ctx meta ...` when spec order, status, or dependencies change.
11. Refresh the epic progress tracker with `ctx epic progress <epic> --write`.

## Mode 3. Attach Spec

Use this mode when linking an existing spec to an epic.

Steps:

1. Read the existing spec docs.
2. Read the epic README when it exists.
3. Prefer `ctx epic attach <epic> <spec>` when available.
4. Set `epic: <epic>` in `.ctx/specs/<feature>/REQUIREMENTS.md`.
5. Keep the current spec slug by default.
6. Use `--rename` only when the user explicitly asks for path churn.
7. Align the child spec with epic goals and non-goals without removing useful standalone context.
8. Preserve task state and review history.
9. Refresh the epic progress tracker with `ctx epic progress <epic> --write`.

## Mode 4. Detach Spec

Use this mode when removing epic membership from an existing spec.

Steps:

1. Read the spec docs.
2. Prefer `ctx epic detach <spec>` when available.
3. Remove `epic:` from canonical `REQUIREMENTS.md` front matter.
4. Keep the current spec slug by default.
5. Use `--rename` only when the user explicitly asks for path churn.
6. Update wording so the spec remains readable as a standalone feature.
7. Preserve task state and review history.
8. Refresh the old epic progress tracker with `ctx epic progress <epic> --write` when the old epic README exists.

## Mode 5. Review Epic

Use this mode when reviewing an epic and linked child specs.

Steps:

1. Read the core `ctx` skill.
2. Read `.ctx/README.md`.
3. Read `.ctx/epics/<epic>/README.md`.
4. Identify linked child specs from `epic:` front matter, not from the README child list alone.
5. Read each linked child spec's `REQUIREMENTS.md`, `DESIGN.md`, `TASKS.md`, and `REVIEWS.md` when present.
6. Review for:
   - gaps in epic coverage
   - unclear child boundaries
   - duplicated or overlapping child scope
   - scope leaks beyond epic goals and non-goals
   - missing dependencies or sequencing problems
   - weak test strategy
   - stale or unresolved open questions
   - stale generated epic progress tracker
7. Report findings first, ordered by severity.
8. Keep code, epic/feature requirements and design, manifest and epic progress unchanged during review. Persist the review and handoff under the core ctx rules; limit TASKS.md edits to review capture and concrete follow-ups.

## Mode 6. Resolve Epic Questions

Use this mode when resolving epic-level decisions.

Steps:

1. Read the epic README and linked child specs.
2. Identify the next highest-priority unresolved question.
3. Present options with pros, cons, and impact.
4. Recommend one option.
5. Use decisions and authorization already provided in the session. Ask only about unresolved choices and wait for the needed answer; question-only turns write no records or commits.
6. After a decision, update the epic README and affected child specs as if the decision had been there from the start.
7. Remove or resolve the open question.
8. Update child tasks when the decision changes scope or implementation work.
9. Update `.ctx/manifest.json` through `ctx meta ...` when ordering, status, or dependencies change.
10. Refresh the epic progress tracker with `ctx epic progress <epic> --write` when child tasks, membership, ordering, status, or dependencies change.
11. Capture qualifying ADRs through `ctx adr ...`, then persist the execution handoff under the core ctx rules.

## Mode 7. Maintain Epic Progress

Use this mode when updating the generated progress section in `.ctx/epics/<epic>/README.md`.

Steps:

1. Read the core `ctx` skill.
2. Read `.ctx/README.md` and `.ctx/epics/<epic>/README.md`.
3. Identify linked child specs from `epic:` front matter, not from the README child list alone.
4. Use `ctx epic progress <epic> --write` after create-spec, attach, move, detach, resequence, close, sync, or task-state changes.
5. Use `ctx epic validate-progress <epic>` during epic review or CI-style checks.
6. Do not manually edit the managed tracker block except through the command.

## Response behavior

When using this skill:

- State the epic and mode you are using.
- Mention child specs that were read or changed.
- Summarize doc, manifest, or task updates.
- Mention validation performed.
- Keep follow-up tasks concrete and only add them when truly needed.

PRDs, TDDs and ADRs are optional context, not epic creation or execution prerequisites. Exact TDD approval planning uses ctx prompt tdd create-epic; rendering creates no epic or pin.
