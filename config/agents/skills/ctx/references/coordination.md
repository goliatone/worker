# Epic and workspace coordination

Apply the core ctx skill's task capture, project policy, ownership and handoff rules throughout these workflows.

Group prerequisite and consumer specs using the planning reference's dependency-ready execution blocks. Batch required changes by package/release before scheduling consumer BE/FE ranges; a parallel wave or shared epic does not satisfy missing contracts or external releases. Record readiness at the actual contract/deliverable boundary, without depending on unrelated owner backlogs.

## Epic rules

Epic support is optional. Specs stay flat under `.ctx/specs/`; do not move or nest specs under `.ctx/epics/`.

Rules:

- Spec epic membership is read from `epic:` front matter in `.ctx/specs/<feature>/REQUIREMENTS.md`.
- Missing `epic:` means the spec is standalone.
- If a spec has an epic, read `.ctx/epics/<epic>/README.md` when it exists before creating, updating, executing, syncing, reviewing, or closing that spec.
- Keep child specs aligned with epic goals, non-goals, ordering notes, dependencies, and open questions.
- Keep child specs readable as standalone feature docs; do not rely on the epic README as the only place where child behavior is defined.
- Treat `.ctx/epics/<epic>/README.md` as contextual documentation, not the authoritative child list.
- Treat the epic progress tracker in `.ctx/epics/<epic>/README.md` as a generated view; canonical state remains in `.ctx/manifest.json`, child spec front matter, and child `TASKS.md`.
- After changing a child spec's task state, manifest status, order, dependencies, or epic membership, refresh the tracker with `ctx epic progress <epic> --write`.
- During review-only workflows, check tracker freshness with `ctx epic progress <epic> --check` and report the needed write command instead of updating it silently.
- Use the companion `ctx-epic` skill for epic creation, child spec creation, attaching or detaching specs, epic reviews, and epic-level question resolution.
- Use `ctx epic ...` commands for epic mutations when available.

### Generated epic automation

Use a versioned policy when an epic workflow needs selected children, resumable spec-scoped conversations, or dependency-ordered parallel waves. Preview first; preview validates the policy and reports the selected specs, wave graph, session and prompt sources, isolation, side effects, and intervention conditions without writing a workflow.

```sh
ctx workflow generate epic <epic> --policy .ctx/workflows/<epic>-policy.yaml --preview
ctx workflow generate epic <epic> --policy .ctx/workflows/<epic>-policy.yaml
```

Representative policy:

```yaml
version: 1
epic: actionable-dashboard
defaults: {agent: codex, session_scope: spec, session_recovery: block}
prompts:
  execute: {mode: run-all}
  review: {file: .ctx/prompts/actionable-review.txt}
  fix: {file: .ctx/prompts/actionable-fix.txt, when: always}
waves:
  - id: queue
    specs: [actionable-task-queue]
  - id: core
    after: [queue]
    concurrency: parallel
    max_parallel: 2
    isolation: worktree
    specs: [actionable-task-metadata, actionable-activity]
```

Rules:

- Put a selected dependency in an earlier wave, or complete it before generation.
- Parallel waves require worktree isolation. Each selected spec owns a distinct provider session and paired application/context worktrees; turns within a spec reuse its session when `session_scope: spec`.
- Shared execute, review, and fix settings may be overridden per spec. `fix: always` runs a fix turn even after a passing review; `fix: findings` runs fixes only while bounded findings remain.
- Persist only bounded attribution and hashes. Prompt bodies and provider transcripts remain transient or provider-owned.
- Inspect lineage, wave progress, sessions, worktrees, integration evidence, and recovery guidance through `ctx workflow status` or Workflow Studio.

## Workspace rules

Workspace support is optional and global. It is for coordinating related repo-local specs that may live in completely different directories.

Rules:

- Default global workspace home is `~/.ctx`; override it with `CTX_HOME` when needed.
- Keep `CTX_DIR` for the repo-local context directory only.
- A workspace feature is the cross-repo unit; a repo epic remains repo-local grouping.
- Cross-repo dependencies live in workspace metadata, not in repo-local `.ctx/manifest.json`.
- Workspace commands may edit files under `~/.ctx`, but repo-local spec and task mutations must continue through the normal repo-local `ctx` workflow.
- Use `ctx workspace feature prompt ...` to delegate prompt generation into the target repo instead of inventing workspace-specific task execution.

Common commands:

```sh
ctx workspace new <workspace> --title "Title"
ctx workspace repo add <workspace> <repo-alias> <repo-path>
ctx workspace feature new <workspace> <feature> --title "Title"
ctx workspace feature attach <workspace> <feature> <repo-alias>:<spec> --role "role"
ctx workspace feature status <workspace> <feature>
ctx workspace feature next <workspace> <feature>
ctx workspace validate <workspace>
```

## Integrated scope and acceptance

After lane integration, the parent assesses canonical scope and applies a reviewed reconciliation preview. Eligible completed scope becomes ready for acceptance; workflow completion cannot authorize accepted Done. Preserve deferred/folded disposition and existing acceptance history, surface pending reconciliation, and keep human acceptance separate from task/range completion.
