# Feature planning

Apply the core ctx skill's task capture, project policy, Document voice, ownership and handoff rules throughout these workflows. Translate briefs and session requests into standalone product and engineering prose; check that “user” refers to a feature actor.

### Mode 1. Create feature context

Use this mode when the user asks to create a spec, start a feature, or scaffold feature docs. Inspect optional architectural context before scaffolding; link existing relevant ADRs when useful. A spec/task remains sufficient.

Steps:

1. Read `.ctx/README.md` if it exists.
2. If the requested spec belongs to an epic, read `.ctx/epics/<epic>/README.md` when it exists.
3. Infer or normalize the feature name into kebab case.
4. Ensure `.ctx/specs/<feature>/` exists.
5. Create these files if missing:
   - `REQUIREMENTS.md`
   - `DESIGN.md`
   - `TASKS.md`
6. Preserve or set `epic:` front matter in `REQUIREMENTS.md` when the spec is epic-linked.
7. Ensure `.ctx/manifest.json` exists when the repo uses manifest metadata, and add or update the feature entry through `ctx meta set`.
8. Fill the files from the user’s brief, current repo context, and epic context when applicable.
9. Do not create ad hoc planning files; explicitly authorized canonical ADRs, review records and handoffs remain allowed under their workflows.
10. Do not create `REVIEWS.md` during feature scaffolding; create it only when a review is actually run.
11. Create `HANDOFFS.md` only after the first material execution report, not as an empty scaffold file.

What to write:

#### REQUIREMENTS.md
Include:
- Summary
- Problem
- Goals
- Non Goals
- Requirements
- Acceptance Criteria

Keep it focused on expected behavior and scope. Do not put implementation detail here.

#### DESIGN.md
Include:
- Summary
- Architecture
- Shared Contract and Parallel Work
- Flow
- Changes Required
- Risks and Tradeoffs
- Testing
- Decisions

Keep it focused on the chosen approach. Do not turn it into a task tracker.

#### TASKS.md
Include:
- Summary
- In Progress
- Next
- Done
- Deferred, if needed
- Task Details grouped by workstream (BE, then FE), with optional phases inside each group

Use concrete tasks with stable IDs. Keep the status sections as a short index, and put the execution context in `Task Details`.

For each task in `Task Details`, include:
- a stable task ID such as `T01`
- a concrete title prefixed with `[BE]` or `[FE]`
- start and integration dependencies, deliverable, and enough context for another agent to execute the task
- owned files and shared-file coordination where useful
- task-specific validation expectations where useful

### Mode 2. Update feature context

Use this mode when the feature already exists and the user wants to refine or revise the docs. Recheck Architectural decision routing when choices are introduced, resolved or reversed.

Steps:

1. Read `.ctx/README.md`
2. Read the current feature docs
3. Check `REQUIREMENTS.md` front matter for `epic:` and read the epic README when present
4. Update `REQUIREMENTS.md` if scope or expected behavior changed
5. Update `DESIGN.md` if the implementation plan changed
6. Update `TASKS.md` to reflect the current work plan, preserving BE/FE groups, prefixes and stable IDs
7. Keep the docs aligned with each other and with epic context when applicable
8. If `.ctx/manifest.json` exists and spec order, status, or dependencies change, update it through `ctx meta ...`
9. Preserve `REVIEWS.md` history if it exists; do not rewrite prior review entries
10. Preserve `HANDOFFS.md` history if it exists; insert new entries below its heading

## Naming guidance

Feature folder names should be:

- short
- descriptive
- stable
- kebab case

Good examples:

- `search-result-highlighting`
- `customer-note-editor`
- `epic-referral-intake`

Avoid:

- `new-feature`
- `stuff-for-mvp`
- `temp-plan-v2`

## Scaffolding and fallback

Prefer the native `ctx spec new` scaffolds and established project formats. They own the default file templates; do not maintain separate template copies in this skill. If native scaffolding is unavailable and direct feature Markdown edits are allowed, use the section shapes in Modes 1 and 2 above. Put start/integration dependencies, owned files, deliverables and the smallest check/stopping condition in each Task Details entry; keep the status index short and synchronized. Deferred stabilization stays in the existing feature docs under project policy.


## Concurrent backend and frontend planning

For every new or wholly unstarted spec, group tasks by workstream: backend first, frontend second. Allocate contiguous initial ranges `T01–TN` for BE and `TN+1–TM` for FE when both are present. Prefix task description text after the ID with `[BE]` or `[FE]` in both the status index and Task Details. These labels describe the work, not the executor; either group may be assigned to any agent or person. Numeric order groups work; explicit dependencies determine execution order.

- Agree on the shared contract in `DESIGN.md` during planning: request/result types, read models, routes, permissions, error/empty states and representative inputs. Publish the compile-ready contract before dispatching independent ranges, using the prerequisite spec or small T00 bootstrap below when needed.
- Group BE work around services, persistence, typed commands, registration and thin HTTP/CLI adapters. Group FE work around presentation models, SSR templates, CSS and browser behavior. Classify by responsibility: server-rendered Go presentation code belongs to FE; business rules and authorization belong to BE.
- Split mixed BE/FE work into separate tasks. Keep BE/FE as the outer Task Details groups, with phases inside a group only when useful. Keep each status section grouped BE then FE; do not make completion of the entire BE range a blanket prerequisite for FE.
- Each detailed task names start dependencies, integration dependencies, owned files, deliverable and the smallest relevant check/stopping condition. Distinguish work that can start against agreed sample inputs from work that needs a live endpoint. State actual blockers rather than promising impossible concurrency.
- `DESIGN.md` records file ownership and integration points; shared contract/registration files have one editing owner during concurrent execution. Coordinate shared task-state and handoff edits, and allow one active task per workstream when parallel execution is requested. Grouping alone does not launch agents or assign executors.
- For authorized replanning of wholly unstarted, undispatched work, keep contiguous BE/FE ranges and update dependencies and references together; check handoffs and external references before changing IDs. Once referenced or dispatched, preserve stable IDs and completed evidence. Prefer a focused follow-up spec for new scope that would break the ranges; an authorized exception must list exact lane IDs instead of advertising contiguous ranges.
- Single-workstream specs include only the applicable group; do not invent work to fill a lane. Assign supporting docs, configuration and checks to the workstream they support.
- Keep validation in the owning implementation task and respect the repository's provisional-feature policy. Two workstreams do not imply a separate broad QA/release phase.

## Dependency-ready execution blocks

Plan for each advertised BE/FE range to finish its declared deliverables without pausing for an unfinished task in another lane, a package release, or an approval. Being able to start from sample inputs is insufficient. Sequential dependencies inside a range are fine; concurrency does not remove real integration dependencies.

Before assigning task IDs, inspect required packages and existing contracts. Group prerequisites by owning repository/package and release boundary, then choose:

- **Prerequisite spec:** use for numerous or complex blockers, difficult isolation, or changes requiring a related package release. Batch all known changes needed from the same package (contracts and concrete implementations) into one coordinated delivery and one reviewed release/adoption boundary. Consumer tasks use that version; do not repeat release approval/pinning in each provider task. Name the release owner and exact consumer readiness evidence. Separate releases need a concrete compatibility or delivery reason. Planning never authorizes commits, tags or publication.
- **T00 bootstrap:** use only for small, local, bounded preparation that makes both lanes independently executable: shared types/ports, representative inputs, registration seams or an already available dependency pin. T00 has one owner, owned files, a focused check and explicit exit criteria for both lanes. List it before BE/FE ranges, classify it by responsibility, and exclude it from both dispatch ranges. An explicitly requested bootstrap-containing range may execute T00 first; only prerequisites outside that selected range must already be complete. Do not hide a multi-package feature or an unreleased dependency in T00. Omit it when prerequisites already exist.

In DESIGN, record the prerequisite spec/T00, available package versions, shared contract and files, and each lane's completion boundary. Every outside dependency must be satisfied before dispatch or moved to an explicit later integration block/spec. For a substantial live-integration dependency, create a focused follow-up spec; for a small integration step, name its owner, prerequisites and focused smoke in the existing plan and exclude it from the independent range. This is delivery work, not an extra QA stage.

FE may finish presentation and transport bindings against published types and representative inputs when that is its declared deliverable. Samples do not prove live integration, backend delivery, or product acceptance. Preserve required live work with an explicit owner and completion check; if FE itself requires live endpoints, supply them first or split that work out. Never mark an integrated task complete on sample-only evidence.

Before declaring a plan ready, walk each proposed run-range from first task to last: can every task finish using ready prerequisites and earlier tasks in its own block, even if the other lane makes no progress? Flag repeated release gates, cross-lane completion dependencies and compile/registration seams that exist only in prose. Fix the plan or state the exact blocked block; do not advertise it as independently executable. Record prerequisites, BE range, FE range and any later integration block in the TASKS summary. Use existing task docs, not extra dependency reports or harnesses.

For started/dispatched plans, preserve IDs, completed evidence and historical handoffs. Describe the exact remaining task set and proposed extraction/mapping before authorized replanning; do not silently renumber or weaken completion criteria. Execution still respects range scope and stop-on-blocker rules. Repair the dependency layout rather than asking an executor to bypass a release or start unrelated work.

Example: a feature needs GitHub, Linear and Jira additions in go-services. Deliver those additions together in an owner prerequisite spec, then review/release once and adopt one version. After any small local contract bootstrap, dispatch consumer BE and presentation FE blocks concurrently. Give live provider integration its actual dependencies and owner; do not append it to an FE range advertised as independent when it still waits for BE.
