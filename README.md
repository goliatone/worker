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
  Without this option, existing differing files are preserved and reported.
- `--skip-macos`: leave Finder and Dock preferences unchanged.
- `--skip-extensions`: copy Insiders configuration without installing extensions.
- `--with-deskflow`: also install the stable Deskflow app from its upstream tap.
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
| Node / pnpm | NVM v0.40.8; keep a supported default Node or install current LTS; pnpm 10.32.1 when absent |
| Go tools | Versioned `gopls`, `dlv`, `staticcheck`, `govulncheck` in `extensions/go-tools.txt`; golangci-lint through Homebrew |
| Git | Identity, 28 aliases, delta, LFS filters, `main`, pull rebase, push defaults, SSH URL rewrite, global ignores |
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

## Reruns and backups

- Homebrew uses `--no-upgrade`, with automatic update and installation cleanup
  disabled. Inherited `HOMEBREW_BUNDLE_INSTALL_CLEANUP` and
  `HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP` are cleared for this run so Bundle cannot
  prune other packages or trust entries. Worker does not uninstall packages or
  start Homebrew services.
- Existing NVM/Oh My Zsh/plugin checkouts and installed editor extensions are kept.
  Public clones bypass global Git URL rewrites so bootstrap does not need SSH keys.
- Git and Zsh snapshots are copied, not appended or linked to the checkout.
  Identical files are untouched. Other existing files, including symlinks, are
  preserved unless `--replace-config` is supplied.
- Replacement backups go into `~/.local/state/worker/backups/config.*/` with a
  `destination.txt` recording the original location. Symlinks are backed up as
  links; their targets are not overwritten. Restore a selected backup manually
  after reviewing its destination. There is no automatic rollback of packages.
- Go tool versions are explicit; updating their manifest deliberately changes
  those binaries. Existing Go binaries are checked for package, version, macOS,
  and CPU architecture; corrupt or incompatible copies are rebuilt for this Mac.
  Existing pnpm and editor extensions are not forcibly upgraded.
- Preferences are written only when different. Worker does not restart apps,
  change the login shell, alter power settings, or launch Docker.
- A failed installation stops setup. Failed editor extensions are listed by the
  CLI; rerunning skips successful installs and retries missing ones.
- Tool manifests work with or without a final newline. Installer subprocesses
  receive empty stdin so they cannot consume the remaining manifest entries.

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
SSH access for the preserved GitHub HTTPS-to-SSH rewrite. Launch Docker and finish
its first-run setup when needed. Reopen Finder or log out to see preference changes.

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
runtime compatibility, native Go binaries, manifests, optional Deskflow selection,
inherited cleanup settings, and deferred authentication;
they do not download packages or modify this Mac's preferences. A real fresh-Mac
installation remains a separate validation step.

`WORKER_HOME` exists only to redirect managed file destinations in tests. It is
not a sandbox: real Homebrew and macOS commands still affect the current machine.
Leave it unset for normal use.
