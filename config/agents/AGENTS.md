# Personal Codex defaults

## Working style

- Follow repository conventions and applicable AGENTS.md instructions.
- Favor simple solutions, focused changes and lightweight tracking.
- Keep docs concise, concrete and current. Update canonical docs instead of
  creating duplicate plans, notes or checklists.
- Explain meaningful tradeoffs briefly. Summarize changes, validation,
  remaining work and how to try the result.

## Git policy

- Do not stage or commit application-repository changes, including code,
  tests, configuration, generated assets and documentation. I will review
  and commit them myself. This also applies to external repositories.
- Do not amend commits, push, create tags or publish releases without my
  explicit authorization.
- Exception: follow the ctx workflow for context-document commits only
  inside a verified, separate nested `.ctx` Git repository. Never let
  context Git operations fall through to the application repository.

## Context workflow

When `.ctx/` exists, use it as the canonical project context system.

- Read `.ctx/README.md`, `.ctx/SKILL.md`, the relevant feature's
  REQUIREMENTS.md, DESIGN.md and TASKS.md, and its newest HANDOFFS.md entry
  before material work. Read linked context relevant to the task.
- Use the installed `ctx` skill and its relevant companion skills.
  Follow current workflow guidance rather than reproducing it here.
- Attach material changes to an existing matching task or capture an
  appropriately scoped task before implementation. Answer-only requests
  do not need tasks or new documents.
- Keep document roles separate:
  - REQUIREMENTS.md: expected behavior and scope.
  - DESIGN.md: implementation approach.
  - TASKS.md: execution status and next actions.
  - REVIEWS.md: persisted findings.
  - HANDOFFS.md: concise continuation state.
- Use stable task IDs and only `[ ]`, `[~]` and `[x]`. Keep repeated task
  entries synchronized; preserve started IDs and completed evidence.
- Respect task dependencies, ownership and the ctx planning conventions.
  Prefer one active task unless parallel work is explicitly intended.

## Supporting context and decisions

- PRDs capture product intent; TDDs capture technical approach across
  delivery slices; ADRs record architectural decisions; epics coordinate
  delivery. These are optional, independently usable records.
- Store feature research, evidence, mockups and legacy records under
  `support/`. Keep canonical PRDs, TDDs and ADRs in their ctx collections.
- Search before creating records. Use the appropriate ctx commands and
  skills for lifecycle changes; preserve approvals, history and source
  baselines. Do not invent approval or silently reverse accepted decisions.

## Validation and closeout

- Use the smallest relevant checks and production-path smoke required by
  project policy. Defer broad stabilization until explicitly requested.
- Update canonical docs as behavior, design and task state change.
  Persist reviews and handoffs through the ctx workflow.
- Reconcile delivery state through ctx. Completed tasks or passing checks
  do not constitute my acceptance; accepted closeout requires my explicit
  authorization.
