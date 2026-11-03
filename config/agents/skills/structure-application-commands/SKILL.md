---
name: structure-application-commands
description: Review, design, implement, or refactor application business logic into services exposed through typed commands, while keeping HTTP, admin, CLI, RPC, UI, cron, and job adapters thin and repositories persistence-only. Use when adding or changing business workflows such as mutations, imports, syncs, repairs, extraction, diagnostics, rebuilds, scheduled tasks, command buses, or when reviewing duplicated transport logic; especially in Go and Goliatone projects using go-command or go-admin.
---

# Structure Application Commands

## Objective

Place reusable business behavior in domain/application services and expose user- or system-triggered workflows through typed commands. Reuse the same command payload and service behavior across transports instead of duplicating policy in handlers, jobs, or repositories.

Apply the pattern proportionally. Use commands for workflows and meaningful mutations; allow request-time reads to call focused read-only services when a command adds no value.

## Respect the Requested Scope

- For a review or diagnosis, inspect and report gaps without changing code.
- For planning, name concrete modules and files using project conventions.
- For implementation, make the changes, add tests, update canonical docs, and run relevant validation.
- Do not widen a targeted change into an application-wide migration unless requested or required for correctness.

## Workflow

### 1. Discover Existing Conventions

Inspect the repository before proposing an architecture:

- Read repository instructions and canonical architecture or feature docs.
- If the repository uses `.ctx`, read `.ctx/README.md` and the relevant `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md`; use the installed `ctx` skill when its workflow applies.
- Locate nearby services, commands, command registration, handlers, repositories, jobs, and tests.
- Check dependencies before selecting a framework. Prefer an existing command bus and service layout.
- Trace at least one complete comparable workflow from transport entry point to persistence or provider integration.

Do not invent a new framework when the project already has a coherent pattern.

### 2. Inventory Business Workflows

Find user- and system-triggered behavior, especially:

- state-changing operations
- imports, discovery, extraction, sync, apply, and repair flows
- diagnostics and rebuilds
- batch or long-running work
- scheduled, queued, CLI, RPC, or admin actions

For each workflow, record the current path:

`trigger -> adapter -> business rules -> repositories/providers -> result`

Flag duplicated rules, direct repository writes from adapters, transport-specific payloads for the same use case, and orchestration hidden inside repositories.

### 3. Establish Boundaries

Use these ownership rules:

| Layer | Owns | Must not own |
| --- | --- | --- |
| Transport adapter | Input decoding, authentication/authorization context, command dispatch, response rendering | Business rules, repository orchestration, domain transitions |
| Typed command | Request/result types, request validation, command identity, execution metadata, service delegation | Domain policy, provider policy, direct multi-repository workflows |
| Service | Domain invariants, business rules, state transitions, repository/provider orchestration, transaction boundaries | HTTP/admin/CLI rendering, command-bus registration |
| Repository | Focused persistence operations and storage mapping | Workflow policy, transport behavior, presentation, cross-use-case orchestration |
| Provider adapter | External-system I/O and protocol mapping | Application workflow decisions |

Validate request shape at the command boundary. Enforce business invariants in the service even when the command has already validated its payload.

### 4. Define the Service

Place services in the project's established application/domain location. In a conventional Go project, prefer names such as:

```text
internal/<app>/<domain>_service.go
```

Give a service cohesive use-case methods rather than creating generic base services. Let it coordinate repositories and providers, enforce rules, own state transitions, and define transaction boundaries where needed.

Avoid moving handler code verbatim into a service. Separate input/presentation concerns from reusable business behavior.

### 5. Define Typed Commands

Place command contracts and handlers beside the domain or in the existing command package. A conventional location is:

```text
internal/<app>/<domain>_commands.go
```

For each workflow:

1. Define a typed request message.
2. Give it a stable command name or ID.
3. Validate required fields, ranges, formats, and mutually exclusive modes.
4. Include only metadata the workflow needs, such as actor, tenant/scope, correlation ID, idempotency key, dry-run/write mode, or batch limit.
5. Define a typed result when callers need structured output.
6. Delegate business behavior to the service.
7. Register the command through the existing runtime or command bus.

Prefer one shared payload across admin, CLI, RPC, cron, jobs, and queues. Scheduled and manual execution should invoke or enqueue the same command contract.

Use separate commands when operations have different permissions, side effects, idempotency, or audit meaning. For example, keep discovery, sync, repair, and apply separate unless an explicit mode remains clearer and preserves those differences.

### 6. Thin the Adapters

Refactor HTTP handlers, admin actions, CLI/RPC endpoints, UI route handlers, cron callbacks, and job consumers so they:

1. Decode and normalize input.
2. Construct actor/scope and other execution metadata.
3. Dispatch a command, or call a read-only service for request-time rendering.
4. Map the typed result or error to transport output.

Do not let adapters write repositories directly except in focused persistence tests or code that is itself a service implementation.

### 7. Register and Wire

Follow the project's existing dependency injection and registration style. Ensure name-based dispatch also registers any required message factory. Keep registration close to other application wiring so commands are discoverable and testable.

### 8. Test the Boundaries

Add tests proportional to the change:

- command payload validation accepts and rejects the expected cases
- command identity remains stable
- command handlers delegate to services and return typed results/errors
- services enforce domain rules and coordinate repositories/providers correctly
- adapters dispatch commands instead of duplicating business logic
- admin, CLI, RPC, jobs, and cron reuse the same payload when multiple transports exist
- registration resolves and dispatches the command
- idempotency, dry-run, scope, permissions, and transaction behavior work when applicable

Prefer service tests for business behavior and narrow adapter tests for binding and dispatch.

### 9. Update Canonical Documentation

Update existing architecture docs, feature specs, and task state so new code cannot silently bypass the boundary. In `.ctx` repositories, preserve the roles of `REQUIREMENTS.md`, `DESIGN.md`, and `TASKS.md`; do not create parallel planning documents.

## Goliatone Go Projects

When `github.com/goliatone/go-command` is already used or is the established project choice:

- Implement its typed message and handler contracts.
- Expose a stable ID from `Type() string`.
- Implement `Validate() error` when request validation is needed.
- Implement `Execute(ctx context.Context, msg T) error`.
- When callers need a result, add `Run(ctx, msg) (Result, error)` and make `Execute` a thin wrapper.
- Delegate from the command handler to a service; do not orchestrate repositories in the handler.
- Reuse the existing registry/runtime patterns for CLI, RPC, cron, jobs, and queues.

Use this shape as a guide, adapting names and error conventions to the repository:

```go
const rebuildSearchCommand = "search.rebuild.v1"

type RebuildSearch struct {
	ActorID       string
	ScopeID       string
	CorrelationID string
	IdempotencyKey string
	DryRun        bool
}

func (RebuildSearch) Type() string { return rebuildSearchCommand }
func (m RebuildSearch) Validate() error { /* validate request shape */ return nil }

type RebuildSearchResult struct {
	Scanned int
	Updated int
}

type RebuildSearchOptions struct {
	ActorID        string
	ScopeID        string
	CorrelationID  string
	IdempotencyKey string
	DryRun         bool
}

type RebuildSearchHandler struct {
	service *SearchService
}

func (h *RebuildSearchHandler) Run(ctx context.Context, msg RebuildSearch) (RebuildSearchResult, error) {
	return h.service.Rebuild(ctx, RebuildSearchOptions{
		ActorID:        msg.ActorID,
		ScopeID:        msg.ScopeID,
		CorrelationID:  msg.CorrelationID,
		IdempotencyKey: msg.IdempotencyKey,
		DryRun:         msg.DryRun,
	})
}

func (h *RebuildSearchHandler) Execute(ctx context.Context, msg RebuildSearch) error {
	_, err := h.Run(ctx, msg)
	return err
}
```

For go-admin applications, inspect and use the actual local APIs for `admin.CommandBus`, `admin.RegisterCommand`, `admin.RegisterQuery`, and `admin.RegisterMessageFactory` where name-based dispatch is required. Verify signatures from installed code rather than guessing them.

Consult nearby Goliatone examples when available:

- `go-admin/admin/command_bus.go` for registration and dispatch
- `go-users/command` for typed business handlers
- project-local commands for CLI, RPC, cron, or job exposure

## Avoid These Failure Modes

- Putting business decisions in handlers, callbacks, or command handlers.
- Treating repositories as application services.
- Creating a command that merely renames an existing transport-specific function while retaining duplicated rules.
- Giving every transport a different payload for the same use case.
- Adding metadata fields with no execution, authorization, audit, or idempotency purpose.
- Hiding distinct permission or side-effect models behind an ambiguous mode flag.
- Introducing a command framework for trivial reads or simple persistence with no workflow behavior.
- Claiming architectural compliance without tests for delegation and service rules.

## Deliver Results

For a review or plan, provide:

- a short summary of current architectural gaps
- the workflows and entry points affected
- concrete files/modules to create or update
- an ordered task list naming service and command files
- risks or open decisions that materially affect the design

For implementation, also provide:

- the code and canonical documentation changes made
- validation and test commands run, with results
- any remaining follow-up work
