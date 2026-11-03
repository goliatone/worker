# Setup and prompt customization

Apply the core ctx skill's task capture, project policy, ownership and handoff rules throughout these workflows.

## Launcher compatibility bridge

The installed `ctx.sh` launcher temporarily translates two high-use legacy entry points and warns on stderr before invoking the native CLI:

```sh
ctx.sh status <feature>          # forwards to: ctx spec status <feature>
ctx.sh run-all-phases <feature> # forwards to: ctx prompt run-all <feature>
```

For the legacy run-all entry point, `--claude` is translated to the native `--agent claude` option. Other trailing arguments are preserved. The launcher rejects a binary selection that resolves back to itself instead of recursing.

The warning uses `lgr warn` when available and falls back to plain stderr. New commands, docs, prompts, and automation must use the canonical noun-first paths directly. No other legacy names are translated.

## Skill installation

The ctx repository owns `skills/ctx`, `skills/ctx-epic`, `skills/ctx-adr` `skills/ctx-prd` and `skills/ctx-tdd`. Installed directories are deployment outputs; edit repository sources instead. `ctx setup skills install` installs the offline bundle shipped with the CLI. Use `ctx setup skills status`, `update --dry-run`, and `update` to inspect and upgrade installed bundled snapshots. Local packages use `ctx setup skill <path-to-SKILL.md>`; identity comes from frontmatter and must match the containing directory.

For development, `ctx setup skills link --source <ctx-repo>/skills` links the bundled skills into `~/.agents/skills`; Claude links to those same installations. Link edits follow the checkout. `--force` explicitly replaces changed or unmanaged installations with recoverable backups; real Claude directories are never replaced. `ctx setup skills uninstall <name>` removes only owned installations and links, never linked sources. Use `--dry-run` before a migration. Skill operations do not update project policy, hooks or shell configuration.

Automatic skill notices run after init, spec creation and prompt generation; refreshed session-start hooks use `ctx setup skills status --notice --json`. Surface a notice to the user and leave updates to their explicit choice. Notices compare the running CLI bundle, report installation paths, preserve prompt stdout and remind at most daily for unchanged state. `CTX_SKILL_NOTICES=0` disables notices; ordinary status remains read-only and unthrottled. `status --source <ctx-repo>/skills` explicitly compares checkout content without claiming it is newer. `installed-newer` means the binary is older; `bundle-different` means recency is unknown. Development links, including `source-changed`, already follow source and need no reinstall. Never overwrite project `.ctx/SKILL.md` in response to a skill notice.

## Codex personal defaults template (optional)

[Personal Codex defaults](../assets/codex/AGENTS.md) is an opt-in template for Codex global instructions. It includes the application commit prohibition and routes to current ctx workflows, including optional support files, PRDs, TDDs, ADRs and epics. This asset is not shared ctx policy, a Claude template or an instruction to modify the current project. Read it only for personal Codex setup or template maintenance.

The maintained source is `skills/ctx/assets/codex/AGENTS.md` in the ctx checkout. The CLI embeds this asset in its bundled prompt catalog; no import, project initialization or skill installation is required:

```sh
ctx store get codex-personal-defaults
ctx store list --filter source:bundled
```

The store resolves a local entry before the bundled fallback. JSON metadata reports `source: bundled` and revision 0 for the shipped copy; its digest identifies the exact content. Bundled defaults follow the running CLI version. Reading a default does not copy it into SQLite.

Direct file retrieval remains available from the checkout or the default shared skill installation:

```sh
# From the ctx checkout:
cat skills/ctx/assets/codex/AGENTS.md

# From any directory, with the default skill root:
cat "$HOME/.agents/skills/ctx/assets/codex/AGENTS.md"
```

For a custom installation root, use the resolved ctx skill path reported by `ctx setup skills status`. Snapshots contain their installed version; development links follow the checkout. Use the existing skill update workflow when a snapshot predates this asset.

Review and merge the template into `${CODEX_HOME:-~/.codex}/AGENTS.md` for global Codex use, or paste it into the Codex custom-instructions setting being used. Preserve existing personal rules and keep repository-specific policy in the repository's AGENTS.md. Installing or reading the skill does not activate this template or authorize overwriting personal instructions.

To customize the named default, create a device-local override with the existing set command:

```sh
ctx store set codex-personal-defaults \
  --file skills/ctx/assets/codex/AGENTS.md \
  --description 'My Codex personal instructions' \
  --tag codex --tag personal-defaults --expected-revision 0
ctx store get codex-personal-defaults
```

Use a file containing the desired changes. The creation guard preserves any existing local entry. Local overrides remain outside project Git and survive binary upgrades; they require explicit refresh. `ctx store del codex-personal-defaults` removes a local override and reveals the shipped copy. Deleting a bundled-only ID returns not found because it has no local row. Retrieval does not activate Codex instructions. Maintain reusable template changes in the repository asset; add future shipped IDs to `internal/ctxstore/bundled.go`.

## Prompt renderings

Prompt templates can be tailored per agent. Use `ctx prompt ... --agent <agent>`; `CTX_PROMPT_AGENT=<agent>` sets a default for prompt-rendering commands.

Prompt templates resolve file by file, so a repository can override one prompt without copying the full prompt directory. Resolution prefers a one-off prompt file, then explicit `CTX_PROMPTS_DIR`, then repo-local `.ctx/prompts`, then CLI-embedded defaults. Within each directory, an agent variant takes precedence over the generic template; a configured generic template takes precedence over a lower-priority directory or embedded agent variant. Installed skill prompt directories are not runtime defaults. Agent templates live under `<prompts>/<agent>/<prompt>.txt`; missing agent templates fall back to the normal prompt, so variants can be added incrementally.

Shared prompt guidance lives in partials under `<prompts>/_partials/*.txt`. Default prompts include `{{CONTEXT_GIT_WORKFLOW}}` so repo-local or one-off prompt templates can customize the main instruction text while still inheriting the context git workflow guidance. Override `.ctx/prompts/_partials/context-git-workflow.txt` only when the repository needs different context git rules.

For one-off rendering, set `CTX_PROMPT_FILE=<path>` or pass `--prompt-file <path>` to prompt-rendering commands. One-off templates still receive the standard replacement values and shared partials.

Generated prompts should carry per-run inputs and tactical execution instructions. Durable workflow policy belongs in the core skill, its focused references, or shared partials, not duplicated in every prompt. Per-run inputs include the feature, task ID or task range, source document or session input, explicit agent choice, epic state, and user-supplied constraints.

Example:

```sh
ctx prompt run-all <feature> --agent claude
ctx prompt task <feature> T03 --prompt-file ./custom-execute-task.txt
```

## Optional Claude loop integrations

The bundled Claude execution prompts use the ctx skill directly and do not require a loop plugin. If the user explicitly chooses an installed loop plugin, configure a project-local `claude/` prompt override or a one-off `--prompt-file`. Document the installed command, a finite iteration limit and a completion marker; stop the outer loop when the ctx review cap or a dependency blocker is reached. Do not assume `/ralph-loop` is available or that a slash command embedded in a headless prompt will invoke a plugin.


## Setup drift

`ctx setup check [--strict] [--json]` inspects managed files without writing. Strict mode requires current managed files and valid declared project overrides; missing/outdated files also fail. Settings checks compare only ctx-managed portions. `ctx setup ownership <asset-id> --policy project --reason "<purpose>"` declares a destination-bound context override; `--policy managed` removes that declaration without changing content or installed hashes. Hook scripts remain managed provider sets; use supported configuration or update maintained hook source. Normal init upgrades exact defaults and preserves unknown files. Never use force as routine conflict resolution.
