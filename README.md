# worker

A repeatable core developer setup for a personal Mac. The configuration snapshot
was captured from the existing workstation on **2026-11-02** and reviewed for
portable paths and embedded credentials.

## Run on the new Mac

Use a native terminal as your normal user. Download this repository or clone it
after installing Xcode Command Line Tools. Worker requests the tools if missing,
then stops so you can finish Apple's installation and rerun it.

Sign in to the **Mac App Store** before installing Amphetamine. Worker installs
it through Homebrew Bundle and `mas`; macOS may request administrator or Apple
Account authentication. If that step fails, complete sign-in and rerun `./make`.
An already-installed copy is kept without upgrading it.

```sh
git clone https://github.com/goliatone/worker.git ~/.worker
cd ~/.worker
./make --dry-run
./make
```

Use your reviewed local checkout until these changes have been committed and
pushed; the GitHub clone above will otherwise contain the older installer.
The entry point also works by absolute path from another directory.

Options:

- `--dry-run`: print planned work without invoking Homebrew, GitHub CLI, Node,
  Go, VS Code, downloads, or preference writes. It does not source user configs
  or create directories. Selected Brewfiles must exist and be readable, but
  package/extension availability is not checked online.
- `--replace-config`: back up differing destination files, then replace them.
  Without this option, existing differing files are preserved and reported,
  except for the automatic legacy Git URL repair and, when a gist is selected,
  the targeted include-hook migration described below.
- `--skip-macos`: leave Finder and Dock preferences unchanged.
- `--skip-extensions`: copy Insiders configuration without installing extensions.
- `--with-deskflow`: also install the stable Deskflow app from its upstream tap.
- `--with-ai` (alias `--ai`): also install Ollama, LM Studio, LM Studio Bionic, and
  Unsloth Desktop; requires Apple Silicon and macOS 14 or later.
- `--with-workflow`: custom workflow scripts, pinned upstream tools, and Go helpers.
- `--with-agents`: coding-agent CLIs, portable settings, and captured shared skills.
- `--with-backend`: PostgreSQL 16, NATS, LocalStack's `lstk`, and development utilities.
- `--with-access`: 1Password/CLI and Tailscale; requires macOS 13+.
- `--with-desktop`: selected desktop apps, Nerd Font, and iTerm profile; macOS 14+.
- `--taps-file FILE`: add GitHub taps from a local list; paths are relative to
  your current directory. This registers taps without installing their packages.
- `--dotfiles-gist URL --dotfiles-revision SHA`: install an exact shared-dotfiles
  revision and migrate recognized Git/Zsh include hooks with backups.
- `--help`: show usage.

To review replacement before applying it:

```sh
./make --dry-run --replace-config
./make --replace-config
```

## Included

| Component | Source / behavior |
| --- | --- |
| Homebrew | Current official Bash installer; native Apple Silicon or Intel prefix |
| Core packages | `extensions/Brewfile`: Git and extensions, Go, Python, uv, pipx, AWS CLI, shell utilities, D2, Pandoc |
| Apps | VS Code Insiders, iTerm2, Docker Desktop, Amphetamine (Mac App Store via `mas`) |
| Optional app | `--with-deskflow`: Deskflow from `deskflow/tap`; `extensions/Brewfile.deskflow` |
| Optional AI apps | `--with-ai` / `--ai`: Ollama, LM Studio, Bionic, Unsloth Desktop; `extensions/Brewfile.ai` |
| Node / pnpm | NVM v0.40.8; keep a supported default Node or install current LTS; pnpm 10.32.1 when absent |
| Go tools | Versioned `gopls`, `dlv`, `staticcheck`, `govulncheck` in `extensions/go-tools.txt`; golangci-lint through Homebrew |
| Git | Identity, 28 aliases, delta, LFS filters, `main`, pull rebase, push defaults, global ignores |
| GitHub CLI | `gh-dash` extension plus captured configuration; installation deferred until `gh auth login` when necessary |
| Zsh | Oh My Zsh, `wezm`, current plugins, zsh-histdb, aliases/functions, optional tool paths, telemetry preferences |
| Insiders | 80 extension IDs, including the captured prerelease channel, settings, keybindings, and snippets |
| macOS | Show dotfiles and all extensions; Finder column view and status bar; Dock auto-hide |

Homebrew owns Go and Python; NVM owns the interactive Node environment. Homebrew
may still install Node as another formula's dependency. NVM loads after Homebrew
initialization so the selected Node takes precedence. Python project dependencies
belong in virtual environments; use uv or pipx for isolated CLI tools.

The selected pnpm 10 release requires Node >=18.12. If an older NVM default is
present, worker stops before installing pnpm and explains how to select LTS; it
does not silently change an existing default. `PNPM_HOME` is on PATH before its
directory exists, so the first global package installation works.

## Custom Homebrew taps

Add one GitHub repository URL per line to `extensions/taps.txt`. The supplied
file contains commented examples; uncomment or replace them with your selections:

```text
# My custom taps
github.com/goliatone/homebrew-tap
https://github.com/nats-io/homebrew-nats-tools
```

```sh
./make --dry-run --taps-file extensions/taps.txt
./make --taps-file extensions/taps.txt
# Combine with other bundles as needed:
./make --dry-run --taps-file extensions/taps.txt --with-backend --with-workflow
```

This still runs the normal core setup. Without `--taps-file`, worker ignores the
list. Empty lists are allowed. Blank lines, surrounding spaces/tabs, and whole-line
`#` comments are ignored; Windows line endings and a missing final newline work.
GitHub URLs may omit `https://` and include `.git` or a trailing slash. Equivalent
entries are deduplicated. Inline comments, credentials, SSH input URLs, URL query
strings/fragments, non-GitHub hosts, and tap-name shorthand are not accepted.

Worker validates the entire list before any installation or Git repair. For
`github.com/goliatone/homebrew-tap`, it derives the tap name `goliatone/tap` and
uses the explicit HTTPS repository URL. Repository spelling is preserved: a
repository actually named `homebree-tap` maps to `goliatone/homebree-tap`; worker
does not silently correct it. Two different repositories mapping to the same tap
name are rejected. Homebrew naming is described in its [tap documentation](https://docs.brew.sh/Taps).

Dry-run prints the plan without invoking Homebrew or checking remote availability
or existing origins. On apply, worker checks all requested installed tap origins
before adding missing taps or installing Brewfile packages. Matching GitHub
HTTPS/SSH origins are kept as-is. Conflicting, unreadable, or ambiguous origins
stop for manual review; worker requires exactly one repository origin, counting
local Git includes and empty URL entries. A scheme-less stored origin is a local
filesystem path and does not match a GitHub repository. Incomplete tap directories
without Git metadata also stop for review. Worker never switches a tap's origin.
CLT installation, Homebrew bootstrap, or the existing Git URL repair may already
have completed.

Reruns skip matching taps; a failed addition stops setup and can be retried with
the same command. Successfully added taps remain installed. Removing a line or
omitting the flag does not untap anything. Worker does not grant whole-tap trust,
upgrade tapped repositories, or install every package they contain. Regular
`brew update` behavior remains independent of worker.

To install a particular package as part of setup, add its fully qualified name
to a selected Brewfile, for example `brew "goliatone/tap/YOUR_FORMULA"`. Private
taps require working Git HTTPS authentication; the list never stores credentials.

## Optional AI apps

```sh
./make --dry-run --ai
./make --ai
# Flags can be combined:
./make --dry-run --with-ai --with-deskflow
./make --with-ai --with-deskflow
```

This runs the normal setup plus the separate `extensions/Brewfile.ai` bundle:

| App | Homebrew cask |
| --- | --- |
| Ollama app and CLI | [ollama-app](https://formulae.brew.sh/cask/ollama-app) |
| LM Studio | [lm-studio](https://formulae.brew.sh/cask/lm-studio) |
| LM Studio Bionic | [lm-studio-bionic](https://formulae.brew.sh/cask/lm-studio-bionic) |
| Unsloth Desktop | [unsloth](https://formulae.brew.sh/cask/unsloth) |

The complete bundle requires **Apple Silicon and macOS 14+**. Worker checks this
before any installs or config repairs, including in dry-run. Bionic is LM Studio's
separate agent app. Unsloth is the Mac desktop app, currently released as a beta;
this does not install the Python training library into your projects. See the
[official Unsloth Mac setup](https://unsloth.ai/docs/get-started/install/mac) for
its desktop, web UI, and library options.

As with the core bundle, `--no-upgrade` keeps existing Homebrew-managed versions.
Without the flag, worker leaves AI apps alone. Worker does not launch the apps,
start servers/login items, download models, or configure accounts. Open the apps
when ready to complete their first-run setup and choose models. Their own update
settings remain independent of worker.

## Optional Deskflow

To include keyboard and mouse sharing in setup:

```sh
./make --dry-run --with-deskflow
./make --with-deskflow
```

The flag adds the [upstream Deskflow tap](https://github.com/deskflow/homebrew-tap)
and trusts its stable `deskflow` cask only. It uses `--no-upgrade`, so reruns keep
installed versions. Without the flag, worker does not install Deskflow or add its
tap; a previously installed copy is left in place. This runs the normal setup too.

After installation, open Deskflow on both Macs. Use the personal Mac as the server
(sharing its keyboard/mouse) and the work Mac as the client, then pair them and
arrange their screens. In System Settings > Privacy & Security, grant Accessibility
to Deskflow and its `deskflow` process, and allow Local Network access when prompted.
See [Deskflow's macOS instructions](https://github.com/deskflow/deskflow#installing-on-macos).
Worker does not launch Deskflow, configure connections, or change macOS permissions.

Older worker snapshots added a blanket GitHub HTTPS-to-SSH rewrite, which can
make Homebrew tap clones fail with `Permission denied (publickey)` before SSH keys
are configured. Homebrew filters `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_NOSYSTEM`, so
passing those variables to `./make` does not reliably fix tap clones.

Current worker detects the exact `url.git@github.com:.insteadOf = https://github.com/`
rule in `~/.gitconfig` before running Homebrew. It automatically backs up the whole
file to `~/.local/state/worker/backups/git-url-rewrite.*/.gitconfig`, records its
original path in `destination.txt`, then removes only that exact rule. No extra
flag or manual Git commands are needed:

```sh
./make --dry-run --with-deskflow
./make --with-deskflow
```

Dry-run only reads the config and reports the planned backup/removal. If Command
Line Tools are missing, it defers the check instead of invoking Apple's Git stub.
Normal runs stop for CLT installation before attempting the repair. Once repaired,
reruns leave the file untouched and do not create another repair backup.

Other values, narrower URL rewrites, file permissions, and explicit SSH remotes
are preserved. Git handles locking and writes; backup or edit failures
stop setup before Homebrew. Matching symlinked or non-writable configs are reported
for manual repair rather than replacing a symlink or editing another target.
Included files (such as `~/.gitconfig.local`), XDG configs, system configs, and other
rewrite rules are outside this targeted migration. If the error persists, inspect
`git config --show-origin --get-regexp '^url\..*\.insteadof$'` for another rule.
The current snapshot no longer contains the blanket rewrite.

## Optional workflow and application bundles

All bundles are opt-in and can be combined with `--ai` and `--with-deskflow`:

```sh
./make --dry-run --with-workflow --with-agents --with-backend --with-access --with-desktop
./make --with-workflow --with-agents --with-backend --with-access --with-desktop
```

| Flag | Installs |
| --- | --- |
| `--with-workflow` | ImageMagick, `ai-shot`, `ctx.sh`, upstream `ctx`/`gengql`/`g`, ctx completion, `mockgen`, `gqlgen`, `swag`, `goi18n`, `gosec`, `actionlint` |
| `--with-agents` | Codex CLI, Claude Code, Cursor CLI; selected settings and nine shared skills |
| `--with-backend` | PostgreSQL 16, NATS server/CLI, `lstk`, golang-migrate, mkcert, cloudflared, sops, ngrok |
| `--with-access` | Current 1Password app, 1Password CLI, Tailscale app |
| `--with-desktop` | Raycast, Rectangle, Bruno, Postico 2, DBeaver, BitstromWera Nerd Font, Worker iTerm profile |

Edit the separate `extensions/Brewfile.*` files to change each bundle. Homebrew
keeps installed versions with `--no-upgrade`; these are package selections, not
an exact lockfile of Homebrew versions. Project SDK versions and project-local
generator pins remain the project's responsibility.

### Custom workflow tools

`extensions/custom-workflow-tools.json` pins clean upstream commits, deliberately
excluding the source Mac's uncommitted changes. `ctx` uses commit `48ce8f603ccb`;
`gengql` uses `f2e1dc24a732` from `auto/go-errors-v0.9.0`; `g` uses release v1.8.0
(`a82e89cc63f8`). The default generator branch has an incomplete dependency
manifest; this published branch was selected after a successful clean build.
The upstream generator command is still `gql-gen`; it is installed as `~/bin/gengql` for PATH
compatibility, but its command interface may differ from the modified local build.

The ctx and go-gql-gen repositories are private. Run `gh auth login` with an account
that can read them, then rerun `--with-workflow`. Without GitHub authentication,
worker defers those two builds and completes the remaining tools. Authentication
does not grant repository access; a denied archive download stops the selected
build with GitHub's error. Source archives are downloaded only during setup,
checked for unsafe paths/links, and built in temporary directories. Go credentials
and private-module settings apply only to the build subprocess; no global Git or
Go authentication settings are written.
The archive request explicitly targets github.com even when `GH_HOST` names a
work GitHub Enterprise server. Builds ignore inherited Git URL overrides and
`GOFLAGS`; downloads ignore `.curlrc` so its output/redirect options cannot alter
the setup operation.

Builds are verified for package and native macOS architecture before installation.
Their commit, architecture, binary hash, and completion hash are recorded under
`~/.local/state/worker/tools/`; matching reruns skip downloads and builds. Existing
custom or differing binaries are preserved unless `--replace-config` is supplied.
Replacements are backed up only after a successful build. That flag also replaces
other differing managed configurations, so review its dry-run before using it.

`extensions/go-workflow-tools.txt` records the Go helper versions observed on the
source workstation. These helpers also build in temporary storage and preserve
differing existing binaries unless replacement is requested. `g` is installed as
a command only; worker does not switch the active Go toolchain. `ai-shot` and
`ctx.sh` are copied with executable permissions into `~/bin`, which worker's Zsh
configuration already places on PATH. The ctx completion is taken from the same
upstream source revision as its binary.
The captured `ai-shot` also propagates ImageMagick failures instead of reporting
output files that were never created.

### Agent settings and skills

`config/agents/` is a reviewed portable snapshot, mapped and checksummed by
`extensions/agent-files.json`. Codex receives the captured model/reasoning settings
and personal AGENTS.md; Claude receives attribution/thinking/output preferences;
Cursor receives editor preferences. Existing files follow the normal preserve /
`--replace-config` backup rules. Account tokens, shell environment overrides,
machine-specific paths, project trust, hooks, plugin state, and MCP connections
are not copied. The obsolete Codex `personality = "pragmatic"` setting is omitted.

Shared skills copied into both `~/.agents/skills` and `~/.claude/skills` are: ctx,
ctx-adr, ctx-epic, go-errors-use, go-errors-migrate, go-admin-dashboard-builder,
go-admin-theme-builder, structure-application-commands, and webcap-agent. Runtime
databases/caches and system/plugin skills are excluded. Local documentation paths
use `$HOME`; the referenced project checkouts must exist when a skill needs them.
Personal artifact-template and project-specific skills are not part of this shared
snapshot. Updating a captured file also requires updating its SHA-256 entry in
the manifest; an unmatched snapshot fails before installing agent files.
All agent destinations are checked before copying settings or skills. A symlinked
parent directory stops this bundle for review without writing through the link.

Sources: [Codex configuration](https://developers.openai.com/codex/config-basic),
[Codex skill locations](https://developers.openai.com/codex/skills),
[Claude settings](https://code.claude.com/docs/en/settings), and
[Cursor CLI cask](https://formulae.brew.sh/cask/cursor-cli).

### Backend, access, and desktop behavior

NATS CLI uses the official `nats-io/nats-tools` tap. LocalStack uses the official
`localstack/tap/lstk` package, following its [current installation guide](https://docs.localstack.cloud/aws/getting-started/installation/);
the older Python `localstack` formula is not installed. `lstk` requires Docker
and account setup when you first use it. Existing data, Docker volumes, certificates,
AWS profiles, SSH keys, and registry credentials are not migrated.

Worker does not start database services, create tunnels, or run `mkcert -install`.
PostgreSQL's package may initialize an empty cluster during installation, and
vendor package installers such as Tailscale may register background components.
PostgreSQL 16 is keg-only; its commands are in `$(brew --prefix postgresql@16)/bin`.
Sign in and configure permissions for access apps manually. The current 1Password
app and Postico 2 may need different licenses from the older installed versions.

The [iTerm dynamic profile](https://iterm2.com/documentation-dynamic-profiles.html)
captures visual settings only, uses the current Nerd Font name, and appears as
**Worker**. Select it in iTerm; existing profiles and the default selection remain
untouched. Browser accounts, application sessions, custom app shortcuts, and full
Xcode/mobile SDKs remain separate migration steps.

## Shared dotfiles from a pinned gist

Create a gist containing `zshrc.shared` and `gitconfig.shared`; optionally include
`zshrc.shared.pre`. Reviewed starter files are in `examples/dotfiles/`. Use the
full 40-character revision from that gist's history:

```sh
./make --dry-run \
  --dotfiles-gist 'https://gist.github.com/YOUR_USER/YOUR_GIST_ID' \
  --dotfiles-revision 'FULL_40_CHARACTER_COMMIT_SHA'

# After review, run the same command without --dry-run.
```

The source URL must be `https://gist.github.com/[USER/]ID`. Raw URLs, moving branch
names, arbitrary destinations, and remote installer scripts are not accepted.
GitHub's [gist revision API](https://docs.github.com/en/rest/gists/gists#get-a-gist-revision)
provides the selected contents. Worker checks the returned gist/revision, requires
complete UTF-8 text, rejects truncated responses, limits file sizes, and validates
Zsh and Git syntax without sourcing the files. It also rejects the legacy blanket
GitHub HTTPS-to-SSH rewrite. Unknown gist files are ignored. These checks are not
a security review: shell configuration executes when the shell later loads it.
Use trusted, reviewed content. Secret gists are unlisted, not private; do not put
credentials in them ([GitHub visibility guidance](https://docs.github.com/en/get-started/writing-on-github/editing-and-sharing-content-with-gists/creating-gists)).

| Gist file | Destination / loading order |
| --- | --- |
| `zshrc.shared.pre` | `~/.config/worker/zshrc.shared.pre`, after base theme/plugin defaults and before Oh My Zsh |
| `zshrc.shared` | `~/.config/worker/zshrc.shared`, after base aliases/functions and before `.zshrc.local` |
| `gitconfig.shared` | `~/.config/worker/gitconfig.shared`, before `.gitconfig.local` |

Selecting a gist explicitly enables a narrow include-hook migration on existing
worker `.zshrc`/`.gitconfig` files. Both layouts are checked before either is
edited; recognized hooks are inserted once with backups, preserving unrelated
content and leaving local overrides last. Symlinked or ambiguous startup configs
and invalid merged syntax stop for review rather than being rewritten. Commented
hooks are not treated as active hooks. Fresh worker snapshots already have
these hooks. Early shared Zsh settings configure initialization; late/local
settings cannot retroactively change plugins that have already loaded.

Dry-run does not download, validate remote content, or change hooks/files. It
reports the intended revision and destinations. Apply downloads and validates
all shared files first. Identical files are untouched; if any shared file differs,
the whole shared update is preserved until `--replace-config` is supplied. That
flag affects all managed configs, not just the gist. Removing the optional early
file from a new revision replaces it with an inert comment under the same backup
policy, so old initialization code cannot remain active silently.

The installed source revision and hashes live in
`~/.local/state/worker/dotfiles.json`. Subsequent setup runs with the same revision
fetch and compare again without rewriting matching files. Shell startup never
performs network requests. A download/validation failure leaves the shared layer
unchanged; preceding core/package setup steps are not rolled back.
The shared files, startup hooks, and receipt are prepared as one group: every
destination is checked and all needed backups and temporary files are prepared
before replacement begins. A caught write failure restores files already changed
in that group. The same protection covers each custom tool's binary, completion,
and receipt, and agent file installation. If rollback also fails, worker reports
the affected paths and retains the original backups for manual recovery.
This is not a transaction across power
loss, forced termination, or simultaneous edits; retain the backups and rerun the
same command after resolving a failure.

## Reruns and backups

- Homebrew uses `--no-upgrade`, with automatic update and installation cleanup
  disabled. Inherited `HOMEBREW_BUNDLE_INSTALL_CLEANUP` and
  `HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP` are cleared for this run so Bundle cannot
  prune other packages or trust entries. Worker does not uninstall packages or
  start Homebrew services.
- Existing NVM/Oh My Zsh/plugin checkouts and installed editor extensions are kept.
  Direct Git clones for NVM and Zsh bypass global/system Git configuration.
  Homebrew tap clones use Homebrew's environment; the targeted legacy Git URL
  repair above runs before Homebrew, including when Deskflow is not selected.
- Git and Zsh snapshots are copied, not appended or linked to the checkout.
  Identical files are untouched. Apart from the targeted legacy Git URL repair
  and the explicitly selected gist hook migration, existing files, including
  symlinks, are preserved unless `--replace-config`
  is supplied.
- Replacement backups go into `~/.local/state/worker/backups/config.*/` with a
  `destination.txt` recording the original location. Symlinks are backed up as
  links; their targets are not overwritten. Restore a selected backup manually
  after reviewing its destination. A file itself named `destination.txt` is saved
  in `original/destination.txt` inside its backup directory to avoid overwriting
  it with recovery metadata. There is no automatic rollback of packages.
- Go tool versions are explicit; updating their manifest deliberately changes
  those binaries. Existing Go binaries are checked for package, version, macOS,
  and CPU architecture; corrupt or incompatible copies are rebuilt for this Mac.
  Existing pnpm and editor extensions are not forcibly upgraded.
- Preferences are written only when different. Boolean writes use `true`/`false`;
  macOS's numeric `1`/`0` readback is treated as equivalent on reruns. Worker does
  not restart apps, change the login shell, alter power settings, or launch Docker.
- A failed installation stops setup. Failed editor extensions are listed by the
  CLI; rerunning skips successful installs and retries missing ones.
- Tool manifests work with or without a final newline. Installer subprocesses
  receive empty stdin so they cannot consume the remaining manifest entries.

If an older checkout stopped at `defaults write ... -bool 1`, update worker and
rerun the same flags, starting with `--dry-run`. Completed installs are kept; no
reset or `--replace-config` is needed. The corrected run applies the remaining
preferences. A failed preference write now names the affected domain and key.

## Configuration snapshot adjustments

`config/` contains the captured settings, with these deliberate changes:

- Embedded shell secrets and the SQLTools database connection block are excluded.
  Auth tokens, SSH private keys, cloud credentials, editor sessions, extension
  storage, and browser data are not copied.
- Git paths use `~`. The missing `git-branches` helper becomes `git branch -avv`;
  DiffMerge/opendiff integration becomes VS Code Insiders diff/merge commands;
  the machine-wide `branch.master` override is removed. Other aliases retain
  their behavior, including `release-tag` targeting `master`.
- Zsh paths use `$HOME`, remove duplicate initialization, and guard optional apps.
  `pwdps` no longer requires `lgr`; `mdfmt` preserves the original on formatter
  failure. History databases and locally built helper binaries are not copied.
- Insiders discovers Go through PATH instead of fixed workstation paths. D2 uses
  `d2`; Go linting uses `golangci-lint-v2` and `--fast-only`. Other editor
  preferences are retained. Snippet JSONC is normalized to JSON.
- Extension versions are recorded as IDs, not obsolete binary versions. New
  installations use Marketplace releases compatible with Insiders. If a captured
  extension has been retired, remove/replace its entry and rerun.
- Oh My Zsh and zsh-histdb use the revisions observed on the source workstation.
  Existing checkouts are not reset or pulled automatically. Oh My Zsh's shell
  updater is disabled for this pinned snapshot; update the framework deliberately.
  New zsh-histdb checkouts also receive the captured `zsh-histdb.patch`, preserving
  your 5000 ms SQLite busy timeout. The patch is applied before the new checkout
  is installed; a failed patch leaves no partial destination. Existing checkouts
  and their local changes are preserved without applying the patch again.

Personal overrides can live in `~/.gitconfig.local`, `~/.zshenv.local`,
`~/.zprofile.local`, and `~/.zshrc.local`. They load last and are never captured
by worker. Change Insiders settings in the app or edit the repository snapshot
and explicitly replace it later. Keep secrets out of this public repository.

## After setup

Open a new terminal, then check the tools you need:

```sh
command -v brew git go node pnpm python3 uv code-insiders
node --version
go version
git config --get core.pager
code-insiders --list-extensions
```

Sign in with `gh auth login`, then rerun worker if gh-dash was deferred. Configure
SSH access if your project remotes use SSH. Launch Docker and finish its first-run
setup when needed. Reopen Finder or log out to see preference changes.

Open [Amphetamine](https://apps.apple.com/us/app/amphetamine/id937984704) to choose
its keep-awake sessions or triggers and whether it starts at login. Worker installs
the app but does not launch it, enable a session, or change sleep/lock settings.

Full Xcode, app permissions, account sign-ins, licenses, databases, Docker volumes,
and project data remain separate migration steps. The core setup does not include
Ruby/RVM, Rust, mobile SDKs, design apps, local-AI stacks, private/personal taps, or
custom local builds such as `ctx`. Existing optional shell integrations remain
guarded for when those tools are installed. iTerm2 is installed with its defaults;
terminal profile migration is not part of this snapshot.

The old Atom, Docker Toolbox, GVM, Ruby/Python version installers, Travis setup,
and executable `worker.local` hook were removed. The known conflicts in the old
Mac's personal Homebrew tap are not modified by worker.

## Validate without installing

```sh
./test.local
```

Requires Bash, Zsh, Python 3, Git, and ShellCheck. Tests use temporary directories
and mocked package managers/system commands. They exercise dry-run purity,
reruns, backups, symlink handling, partial failures, fresh Homebrew bootstrapping,
runtime compatibility, native Go binaries, manifests, optional Deskflow/AI selection,
AI platform checks and retries, inherited cleanup settings, automatic Git URL
repair/backup/failure handling, deferred authentication, and preference failures
and retries. Portable setup tests cover selected bundles, executable backups,
clean upstream builds with mocked downloads, gist revision/content validation,
hook migrations, actual Git/Zsh precedence, and credential/runtime exclusions. On macOS, a regression test also invokes real `defaults` against a
disposable absolute plist path in a temporary directory, checks boolean types and
numeric readback, then verifies that reruns leave the file unchanged. Tests do not
download packages or change Finder, Dock, or global preferences. When Homebrew is
available, an offline smoke test copies its launcher and substitutes a URL probe
for the package manager to exercise the real environment filter. A real fresh-Mac
installation remains a separate validation step.

`WORKER_HOME` exists only to redirect managed file destinations in tests. It is
not a sandbox: real Homebrew and macOS commands still affect the current machine.
Leave it unset for normal use.
