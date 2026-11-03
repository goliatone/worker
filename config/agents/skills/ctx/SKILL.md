---
name: ctx
description: Manage feature context and material repository work for projects that use .ctx feature specs. Use this skill to route work through tasks, create or update specs, execute tasks, sync docs, run reviews, and persist session handoffs. Read-only answers that produce no durable project artifact do not require task capture.
---

# ctx skill

## Purpose and routing

Use this skill in repositories with `.ctx/`, or when the user asks to create that workflow. Use `.ctx/` as the canonical feature context system. Read `.ctx/README.md`, project `.ctx/SKILL.md`, applicable agent policy, and the relevant feature's requirements, design, tasks and newest handoff before material work. Project conventions and the user's current scope govern this generic workflow; do not replace project policy when updating installed skills.

Read only the reference needed for the current operation, relative to this skill directory:

- [Feature planning](references/planning.md): create, revise or review feature plans, choose file shapes and naming, and define dependency-ready BE/FE blocks, prerequisite specs/T00 and batched package releases.
- [Epic and workspace coordination](references/coordination.md): epic-linked work, generated workflows, waves, cross-repo membership and dependencies. For epic-linked execution, read the epic rules and its README; load automation details only when generating or running that workflow.
- [Bugs, support archiving and history](references/maintenance.md): native bug lifecycle, moving external support documents, or configuring metadata capture.
- [Setup and prompt customization](references/setup-and-prompts.md): installing/updating skills, retrieving the optional Codex personal-defaults template, resolving prompt overrides, or using the legacy launcher and optional loop plugins.

Use the companion `ctx-adr`, `ctx-prd`, `ctx-tdd` and `ctx-epic` skills for their respective lifecycle operations. Task execution, review, ownership and handoff rules remain here.

## Document voice

Write ADRs, PRDs, epics, specs, proposals, reviews and handoffs as the responsible developer or project team, in prose that stands on its own outside the conversation.

- State the problem, requirements, decisions and rationale directly. Do not narrate the assistant/requester exchange or write “the user requested”, “you asked”, “as discussed” or “I will implement”.
- In authored product and technical prose, “user” means the feature's end user. Name concrete roles when useful: operator, administrator, maintainer, product owner or decision owner. Refer to the requester by a project role only when attribution matters.
- Translate requests into durable requirements without inventing rationale, evidence, consensus or approval. Keep proposals, assumptions and accepted decisions distinct. Use “we” only for the project team when appropriate.
- Preserve source quotations and historical/provenance records; identify required attribution by role or source. This voice rule does not change authorization, lifecycle guards or immutable evidence. Review new or revised prose for conversation-dependent wording before saving; review-only work reports issues without rewriting the source.

For example, replace “The user explicitly requested shared infrastructure so later document types can reuse it” with “Shared document infrastructure must support reuse by later document types.”

## Context git workflow

`ctx init` initializes an idempotent nested git repo under `.ctx/.git` for context-document history. This repo is separate from the application repository so specs, epics, manifest changes, and review logs can be committed at meaningful workflow moments without mixing them with implementation diffs.

Rules:

- In orchestrated child lanes, leave all commits, manifest updates, epic progress and handoff persistence to the parent. This exception takes precedence over general commit, refresh and handoff instructions throughout this skill and its references. Return structured continuation data instead.
- Resolve the context directory to an absolute path. Before context Git operations, require its `.git` directory or worktree file and verify `git -C <context-dir> rev-parse --show-toplevel` resolves to that directory. If either check fails, stage and commit nothing; report it and suggest `ctx init`. Never let Git discover the parent application repository.
- Quote paths for the shell. Use `git -C <context-dir> status --short` before and after context edits. Stage only owned paths with `git add -- <paths>` and commit them with `git commit --only -m "ctx(<feature>): <summary>" -- <paths>` in the verified context repository; preserve unrelated staged changes.
- Commit `.ctx` changes after meaningful milestones such as creating a spec, starting or completing a task, syncing docs, recording a review or handoff, resolving a decision, refreshing epic progress, or closing a feature.
- Use messages like `ctx(<feature>): create feature plan`, `ctx(<feature>): complete T03 validation`, or `ctx(<feature>): record implementation review`.
- Do not commit `.ctx/history/` unless the user explicitly asks; it is local workflow telemetry and `ctx init` ignores it in the context repo.
- If there are no context changes to commit, report that instead of making an empty commit.

## Core rules

- Treat `.ctx/` as the canonical feature context system when it exists.
- Treat `.ctx/.git` as the context-document history repo when it exists; commit meaningful context changes there separately from application code changes.
- Do not create ad hoc markdown files like `plan.md`, `notes.md`, `todo-v2.md`, `implementation-thoughts.md`, or similar files unless the user explicitly asks for them.
- Keep docs concise, concrete, and current.
- Prefer updating canonical docs over creating new docs.
- Keep file roles separate:
  - `.ctx/manifest.json` = optional machine-readable project metadata for spec ordering, status, and dependencies
  - `.ctx/history/events.jsonl` = optional machine-readable workflow metadata for tooling and timelines
  - `.ctx/history/state.json` = optional tiny current-context cache for tooling
  - `.ctx/history/archive/` = optional compressed rotated workflow event logs
  - `.ctx/bugs/` = optional repo-scoped cross-feature bug records and a rebuildable local bug index
  - `.ctx/epics/<epic>/README.md` = optional initiative-level context for grouped specs, including a generated epic progress tracker when present
  - `~/.ctx/workspaces/<workspace>/workspace.json` = optional global metadata for cross-repo workspace features
  - `~/.ctx/workspaces/<workspace>/features/<feature>.md` = optional human-readable cross-repo feature context generated from workspace metadata
  - `~/.ctx/bugs/` = optional global cross-project bug records and a rebuildable global bug index
  - `.ctx/adrs/` = canonical architectural decisions, alternatives, rationale and lifecycle status
  - `REQUIREMENTS.md` = what the feature must do
  - `DESIGN.md` = how the feature will be built
  - `TASKS.md` = execution status and next actions
  - `REVIEWS.md` = optional persisted review history for spec reviews, implementation reviews, and review-fix summaries
  - `HANDOFFS.md` = optional-on-first-use execution continuation log; concise state for the next session, not a transcript or replacement for tasks and reviews
  - `support/` = optional feature-scoped supporting context such as legacy ADRs, bug reports, research, mockups and evidence that should be findable without becoming a canonical living doc

Manifest `status: active` means in-flight delivery work, not a single global focus. Multiple specs may be active concurrently when they are orthogonal work lanes such as backend, frontend, or infra, or owned by different agents. Use `ctx meta set <feature> --lane <lane> --owner <agent>` to make that concurrency explicit, inspect it with `ctx meta show` or `ctx meta show --json`, and use `ctx current --lane <lane>` or `ctx current --owner <agent>` when resolving scoped focus. Untagged active specs share the implicit `default` lane, so multiple untagged active specs still indicate a likely stale or ambiguous state. Doctor repair preserves planned inactive lanes; it only rewrites active state for same-lane conflicts or explicit `[~]` task evidence.

## Spec delivery lifecycle

Task completion and product acceptance are separate. `ready` means eligible current scope is complete and awaits acceptance; `done` requires explicit authorized human acceptance bound to current scope and assessment revisions. Legacy done remains acceptance-unknown. Preserve folded/deferred disposition and acceptance history; empty scope and unavailable eligibility do not establish completion. Lane conflicts are diagnostic.

After canonical task changes, range completion, integrated workflow completion, review fixes or document synchronization, inspect `ctx spec assess <feature>` and `ctx spec reconcile <feature> --check`. Apply only the reviewed bounded preview with `--apply --preview-revision <revision> --idempotency-key <key>`. Task callbacks may report reconciliation pending after a successful task write; inspect and retry reconciliation without repeating the task mutation. Reopen canonical tasks for unresolved review findings, then assess again.

Use guarded `ctx spec ready/reopen/defer/fold` with the current `--expected-revision`; new dispositions require `--reason`, and folding also requires `--folded-into`. Explicit accepted closeout uses `ctx spec close <feature> --accept --expected-revision <revision> --scope-revision <scope> --reason <reason>` after authorized human intent. Agents, doctor, workflow and scheduled callers must not manufacture that intent. `ctx meta set --status done` is not a closeout path. Metadata-only order/dependency changes retain `ctx meta ...` and validation.

Legacy v1 reads remain available. New lifecycle writes require explicit migration; report that prerequisite without migrating or expanding task scope automatically. Never derive acceptance from checkboxes, prose handoffs or a successful test run.

## Managed setup ownership

Keep reusable setup behavior in maintained source; do not patch installed hook scripts as the sole implementation. Project conventions belong in AGENTS.md / CLAUDE.md. After setup-related changes, rebuild/install the source and run `ctx setup check --strict` before declaring the work complete; use JSON for per-asset source, destination, hashes and repair guidance. Do not run this check for unrelated feature work or alter unrelated installations to make it pass.

Declare intentional context-file customization with `ctx setup ownership <asset-id> --policy project --reason "<purpose>"`. This preserves that destination during init, including force. Returning it to `--policy managed` removes only the declaration; reconcile content before updating. Never replace installed baseline hashes with custom bytes. Use `ctx init --dry-run` for context plans plus read-only hook/settings/completion diagnostics.

## Helper resolution

When the workflow says to use `ctx`, do not rely only on shell aliases. Agent tool calls may run in non-interactive shells that do not source `.zshrc`.

Resolve the helper in this order:

1. `$CTX_CLI_BIN` when set and executable.
2. Repo-local `./ctx` when executable.
3. `ctx` found on `PATH`.

Use the resolved executable path. The `ctx.sh` compatibility launcher translates legacy command names but needs the same native binary; it cannot repair a missing CLI. If unavailable, edit only feature Markdown, reviews and handoffs where allowed. Record required manifest/ADR/PRD/epic commands as remaining work rather than bypassing their guarded mutations.

## Prompt execution contract

When executing generated prompts:

- Read `.ctx/README.md`, project `.ctx/SKILL.md`, applicable agent policy, and the relevant feature docs before execution. Derive paths from the current repository and configured context directory.
- Read the newest `HANDOFFS.md` entry when it exists and reconcile its continuation with current tasks, reviews, Git state, and source before acting.
- Do not write code until `DESIGN.md` and `REQUIREMENTS.md` for the feature have been read.
- Treat task status sync as updating both the status index and the matching Task Details entry when both exist.
- Follow declared start/integration dependencies; BE/FE groups and numeric IDs do not impose execution order or authorize parallel agents. For a task range, stay within the selected numeric IDs and report unfinished outside dependencies.
- Before dispatching a range, verify prerequisites outside the selected range, including prerequisite specs, T00 and external release/adoption gates, are complete; otherwise report the blocked range. If T00 or another prerequisite task is explicitly inside the selected range, execute it first in dependency order, then continue after its checks pass. Never expand the range to include missing prerequisites. Follow the planning reference when repairing the layout, without changing task scope or completion criteria during execution.
- Run the smallest checks required by the task and project policy, with at most 3 review/fix cycles per task or declared review checkpoint unless the user explicitly asks for more. Task completion is not user acceptance.
- Mark tasks `[x]` only after scoped checks and required fixes pass. If blocked or high/medium issues remain at the cap, stop the run, start no further task, and record remaining work without claiming completion; reopen affected tasks if integrated review finds unresolved issues.
- Update manifest state only when delivery state, order, dependencies, or epic membership changed.
- Refresh epic progress when docs, task state, manifest state, or epic membership changed.
- Before the final response, persist a structured handoff in the affected feature's `HANDOFFS.md`; orchestrated child lanes return handoff data to their parent and the parent writes one integrated entry.

## Work intake and implicit task capture

Material repository work must be attached to a task before meaningful project changes begin, even when the user did not name a feature or task explicitly. This includes implementation, fixes, refactors, persisted reviews, investigations that produce durable findings, doc changes, migrations, generated artifacts, and project configuration changes.

Inspect optional architectural context under Architectural decision routing; ordinary work does not require an ADR.

Routing rules:

1. Use an explicitly named feature and task when provided.
2. Otherwise search the likely feature's open tasks and reuse a matching open task instead of creating a duplicate.
3. Otherwise choose the narrowest existing spec whose requirements or design owns the requested behavior, add a concrete task with the next stable ID, and mark it `[~]` before meaningful changes.
4. If the request defines a coherent new feature, contract, data model, architecture change, or multi-area behavior, create a dedicated feature context instead of hiding it in a catch-all.
5. If the work is material but has no natural feature home, lazily create or reuse the standalone `project-operations` spec and add the task there. Keep its requirements and design generic and concise; it is for repository maintenance, tooling, chores, and one-off project work, not undeclared product features.

Use `ctx task list <feature>` and `ctx task get <feature> <task-id>` to check for a matching open task. Prefer `ctx task create <feature> "<concrete title>" --state doing` when available so the CLI allocates the next stable ID atomically. Add `--type bug` for defect work and `--type epic` only for an actual epic queue item; omit `--type` for ordinary tasks. If `task create` is unavailable, use `ctx task add`, preserve the equivalent `[type: bug]` or `[type: epic]` metadata in both owned occurrences when applicable, then run `ctx task set ... doing`. Keep rich status-index and Task Details entries synchronized.

A `ctx bug create` record does not itself create a Work board item. Create or reuse the corresponding feature task with `--type bug`.

Do not create a synthetic task for a conversational explanation, status check, or read-only inspection that produces no durable project artifact. If a read-only investigation becomes a persisted review, decision, bug record, evidence file, or follow-up implementation plan, capture or reuse a task before writing that artifact.

## Architectural decision routing

PRDs, TDDs, ADRs and epics are optional and independently usable. A feature spec and actionable task are sufficient for project work; absent collections are normal empty state. No supporting document or approval is an automatic creation, execution or acceptance prerequisite. Explicit task dependencies and project authorization still apply.

For a significant architectural choice, inspect existing decisions and recommend an ADR when it helps preserve rationale. Record unresolved choices directly in DESIGN as assumptions or open questions unless ADR management is explicitly authorized. Optional advice is not a blocking lifecycle action. If ADR work is authorized, use ctx-adr and guarded native commands; reuse existing identities and never silently reverse accepted decisions. Drafts record proposals without accepting them or authorizing implementation. Review-only work reports findings without mutating decisions.

TDDs own technical approach across delivery slices, PRDs own product intent, ADRs own individual decisions, epics coordinate delivery and specs own executable scope. Use ctx-tdd for technical records and exact source baselines. Ordinary associations grant no authority. Rendered planning context creates no records, pins, approvals or work; exact approved evidence selection and explicitly unapproved draft planning remain distinct.

## Task state rules

Use only these task markers in `TASKS.md`:

- `[ ]` not started
- `[~]` in progress
- `[x]` done

Rules:

- Mark a task `[~]` only when actively working on it now
- Mark a task `[x]` only when it is complete
- Prefer one active task at a time unless parallel work is clearly intended
- Use stable task IDs like `T01`, `T02`, `T03`
- Write tasks as concrete actions, not vague labels; apply the BE/FE grouping and prefix rules in the planning reference
- For rich task files, keep repeated task entries synchronized when the same task appears in the status index and in `Task Details`
- Apply the work-intake rules above when the user did not provide a task; implicit task capture is part of the normal skill workflow, not an optional prompt flag.

Prefer the grouped task command for task operations:

```sh
ctx task list <feature>
ctx task get <feature> T01
ctx task next <feature>
ctx task add <feature> T03 "Do the work"
ctx task set <feature> T01 doing
```

Legacy aliases such as `tasks`, `next-task`, `add-task`, and `set-task` are intentionally unsupported.

## Execution handoff

Use this mode at the end of every material execution, including task, task-range, run-all, spec creation/update, sync, close, support archive, review, fix, and decision-resolution work.

Rules:

- Store handoffs in `.ctx/specs/<feature>/HANDOFFS.md`.
- Handoff persistence is default-on for material execution; do not wait for an opt-in prompt flag. Question-only turns write no records or commits. After applying an authorized decision, persist the resulting handoff. Use existing session decisions; ask only for genuinely unresolved choices.
- Create the file on first use with the heading `# Handoff Log`.
- Insert new entries directly below the heading so newest entries appear first; preserve older entries.
- Use stable IDs in the form `HO-YYYY-MM-DD-NN`.
- Keep entries concise and operational. Do not copy transcripts or full review findings.
- For multi-feature work, write one handoff per affected feature. Epic-only material work uses the feature task home selected by work intake, normally `project-operations`, for its review and handoff.
- For orchestrated work, child lanes must not write competing handoffs; they return structured state and the parent persists the integrated entry.
- Print a terminal report that names the handoff ID and path and agrees with the stored outcome, validation, remaining work, and continuation action.
- Commit the handoff with the execution's other `.ctx` changes at the meaningful milestone.

Use this entry shape:

```md
# Handoff Log

## HO-YYYY-MM-DD-NN Short execution scope
Date: YYYY-MM-DD
Feature: feature-id
Task: T01 or n/a
Status: complete, partial, blocked, or review-only
Review: optional SR-*, IR-*, or FX-* reference

### Outcome
What this execution established or delivered.

### Changes
Important code and context artifacts changed.

### Validation
Commands/checks run and their outcomes.

### Remaining Work
Only unresolved work, risks, or blockers; state `None` when complete.

### Continuation
The exact next task, review/fix pass, blocker-resolution action, or `None`. Include the next `ctx prompt ...` command when applicable.
```

## Operating modes

For creation and updates, read [Feature planning](references/planning.md). For archives and history, read [Bugs, support archiving and history](references/maintenance.md).

### Mode 3. Execute a task

Use this mode when the user asks to implement work from `TASKS.md`.

Steps:

1. Read `.ctx/README.md`
2. Read:
   - `.ctx/specs/<feature>/REQUIREMENTS.md`
   - `.ctx/specs/<feature>/DESIGN.md`
   - `.ctx/specs/<feature>/TASKS.md`
   - the newest `.ctx/specs/<feature>/HANDOFFS.md` entry when present
3. Check `REQUIREMENTS.md` front matter for `epic:` and read the epic README when present
4. Find the target task by ID or by matching description
5. Mark the selected task as `[~]`
6. Implement the task
7. Update `DESIGN.md` if implementation decisions changed materially
8. Update `REQUIREMENTS.md` if scope or behavior changed
9. Run the task-scoped checks and bounded review/fix cycles; mark `[x]` only when those pass and the task is complete
10. Assess task completion and preview guarded reconciliation under Spec delivery lifecycle; update order/dependencies through `ctx meta ...` only when changed
11. If the spec belongs to an epic and task or manifest state changed, run `ctx epic progress <epic> --write`
12. Add follow up tasks only when they are truly needed
13. Persist the execution handoff and name its ID and path in the final response

Execution rules:

- Do not silently ignore the docs
- Do not implement before reading `DESIGN.md` and `REQUIREMENTS.md`
- Do not implement work that contradicts the stated requirements unless the user asks to change scope
- When both a status index and Task Details entry exist, mark the task `[~]` or `[x]` in both places
- Review and fix high or medium bugs, logic errors, and requirement gaps for up to 3 cycles per task
- If high or medium issues remain after 3 cycles, stop and report the unresolved issues
- Keep changes small and attributable to the task when possible
- Do not finish with terminal-only state; follow the Execution handoff section

### Mode 4. Sync docs with code

Use this mode when the user asks to reconcile docs with current implementation.

Steps:

1. Read the feature docs
2. Check `REQUIREMENTS.md` front matter for `epic:` and read the epic README when present
3. Inspect the current implementation
4. Compare code against requirements, design, tasks, and epic context when applicable
5. Update docs to match reality
6. Update `.ctx/manifest.json` through `ctx meta ...` when spec order, status, or dependencies no longer match reality
7. If the spec belongs to an epic and docs or manifest state changed, run `ctx epic progress <epic> --write`
8. Remove stale, misleading, or duplicated task state
9. Do not create ad hoc planning files; preserve required canonical ADRs, reviews and handoffs

### Mode 5. Review and persist findings

Use this mode when the user asks for a spec review, implementation review, or to fix review findings.

Rules:

- `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md` remain the canonical living feature docs; ADRs own architectural decisions. Check Architectural decision routing and report missing records, stale decision status or unlinked reversals. Review-only work does not mutate ADRs.
- If the spec has `epic:` front matter, read the epic README when present and include epic alignment in the review
- Check BE/FE grouping, prefixes, executor neutrality, shared contracts, file ownership and start/integration dependencies; walk each advertised range through completion, checking prerequisite specs/T00, batched package releases and cross-lane integration blockers under the planning reference
- `REVIEWS.md` is an optional log of review artifacts, not a replacement for the canonical docs
- `.ctx/manifest.json` should be reviewed for stale order, status, and dependencies, but review-only prompts should report needed `ctx meta ...` commands instead of silently changing metadata
- Epic progress trackers should be checked for freshness during review-only prompts; report `ctx epic progress <epic> --write` if stale instead of writing it
- Create `REVIEWS.md` on first review if it does not exist
- Keep `REVIEWS.md` human-readable markdown with the heading `# Review Log`
- Insert new entries below the heading so newest entries appear first
- Preserve older entries
- Use stable IDs:
  - `SR-YYYY-MM-DD-NN` for spec reviews
  - `IR-YYYY-MM-DD-NN` for implementation reviews
  - `FX-YYYY-MM-DD-NN` for fix passes
- Print the review or fix summary to stdout and persist the same content in `REVIEWS.md`
- Keep review-only code, requirements, design, ADRs, manifest and epic progress unchanged. Limit `TASKS.md` edits to capturing the review and its concrete follow-ups; do not mark unrelated work complete.
- Persist a concise handoff that references the review or fix ID and records the exact continuation action; do not duplicate full findings in the handoff

Review/fix cycle rules:

- A review/fix cycle compares implementation against requirements, design, task scope, and tests
- Fix confirmed high and medium bugs, logic errors, and requirement gaps
- Run at most 3 review/fix cycles unless the user explicitly asks for more
- If high or medium issues remain after the cap, record them in the report or `REVIEWS.md` instead of continuing indefinitely

### Mode 7. Close out a feature

Use this mode when the feature is effectively done.

Steps:

1. Confirm requirements match shipped behavior
2. Confirm design reflects the actual implementation
3. Confirm completed tasks are marked `[x]`
4. Move leftover items to Deferred if they are intentionally not being shipped now
5. Leave the feature folder in a clean final state
6. Assess and reconcile current scope; preserve ready until explicit authorized human acceptance. Persist the closeout handoff with the exact acceptance or remaining-work continuation.

## Decision rules

When choosing what to update:

- If expected behavior changed, update `REQUIREMENTS.md`
- If implementation approach changed, update `DESIGN.md`
- If execution status changed, update `TASKS.md`
- For delivery status, use shared assessment and guarded lifecycle commands; for order/dependency changes, use `ctx meta set` or `ctx meta move`
- Manifest dependencies must point to known specs that appear earlier in delivery order.
- After changing manifest metadata, run `ctx meta validate`

When choosing whether to create a new feature folder:

Create one when the work changes one or more of these:

- user facing behavior
- UI flow
- API contract
- data model or schema
- architecture
- multiple code areas
- rollout or migration behavior

Do not force a full feature folder for tiny changes such as:

- typo fixes
- isolated refactors
- one line config changes
- minor test updates

## Response behavior

When using this skill:

- State which feature you are working on
- Mention whether you are creating context, executing a task, or syncing docs
- Summarize what changed
- Mention any new follow up tasks only if needed
- Name the persisted handoff ID and path after material execution
- Keep explanations concise and practical

## Guardrails

- Do not invent files outside the `.ctx` workflow unless there is no canonical place for the information
- Do not let `TASKS.md` become a second design doc
- Do let `TASKS.md` carry execution context, relevant files, and validation notes for individual tasks
- Do not let `DESIGN.md` become a backlog
- Do not let `REQUIREMENTS.md` drift into code level detail
- Keep the system lightweight
- If the process starts creating more documentation than clarity, simplify

## Decisions and product requirements

Use `ctx-adr` for canonical `.ctx/adrs/` decisions and guarded lifecycle commands; preserve legacy support ADR identities unless adoption is explicitly requested. Use `ctx-prd` for `.ctx/prds/`, immutable approval evidence and explicit spec/epic pins. Rendering planning context creates no work and authorizes no acceptance or implementation. Feature requirements remain the executable scope.
