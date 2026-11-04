#!/usr/bin/env bash
# Shared globals below are consumed by sourced modules.
# shellcheck disable=SC2034
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DRY_RUN=0
REPLACE_CONFIG=0
SKIP_MACOS=0
SKIP_EXTENSIONS=0
WITH_DESKFLOW=0
WITH_AI=0
WITH_WORKFLOW=0
WITH_AGENTS=0
WITH_BACKEND=0
WITH_ACCESS=0
WITH_DESKTOP=0
DOTFILES_GIST=""
DOTFILES_REVISION=""
TAPS_FILE=""
export PYTHONDONTWRITEBYTECODE=1
WORKER_HOME=${WORKER_HOME:-$HOME}
WARNINGS=0

usage() {
  cat <<'EOF'
Usage: ./make [options]

  --dry-run         Print the plan. No downloads, installs, config writes or defaults changes.
  --replace-config  Back up and replace differing config files (default: preserve them).
  --skip-macos      Leave macOS preferences alone.
  --skip-extensions Install Insiders configuration without installing extensions.
  --with-deskflow    Also install Deskflow for sharing a keyboard and mouse between computers.
  --with-ai, --ai    Also install Ollama, LM Studio, Bionic, and Unsloth Desktop (Apple Silicon, macOS 14+).
  --with-workflow   Install captured helper scripts and pinned Go helpers.
  --with-agents     Install coding-agent CLIs and portable settings/skills.
  --with-backend    Install PostgreSQL 16, NATS, LocalStack CLI, and development utilities.
  --with-access     Install 1Password/CLI and Tailscale (sign-in remains manual).
  --with-desktop    Install selected desktop apps, font, and an iTerm dynamic profile.
  --taps-file FILE  Add GitHub Homebrew taps from a local repository-URL list.
  --dotfiles-gist URL  Install shared dotfiles and migrate recognized include hooks with backups.
  --dotfiles-revision SHA  Required full revision for --dotfiles-gist.
  --help            Show this help.

Run as your normal user. Homebrew may request administrator access when needed.
EOF
}

while (( $# )); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --replace-config) REPLACE_CONFIG=1 ;;
    --skip-macos) SKIP_MACOS=1 ;;
    --skip-extensions) SKIP_EXTENSIONS=1 ;;
    --with-deskflow) WITH_DESKFLOW=1 ;;
    --with-ai|--ai) WITH_AI=1 ;;
    --with-workflow) WITH_WORKFLOW=1 ;;
    --with-agents) WITH_AGENTS=1 ;;
    --with-backend) WITH_BACKEND=1 ;;
    --with-access) WITH_ACCESS=1 ;;
    --with-desktop) WITH_DESKTOP=1 ;;
    --dotfiles-gist|--dotfiles-revision|--taps-file)
      [[ $# -ge 2 && -n "$2" && "$2" != --* ]] || { printf 'Missing value for %s\n' "$1" >&2; exit 2; }
      case "$1" in
        --dotfiles-gist) DOTFILES_GIST=$2 ;;
        --dotfiles-revision) DOTFILES_REVISION=$2 ;;
        --taps-file) TAPS_FILE=$2 ;;
      esac
      shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# All modules share one environment; none source the user's shell configuration.
WORKER_LOADED=1
# shellcheck source=utils.sh
source "$ROOT/utils.sh"
trap 'printf "Worker stopped at %s:%s. Resolve the error and rerun.\n" "${BASH_SOURCE[0]}" "$LINENO" >&2' ERR

if [[ -n "$DOTFILES_GIST$DOTFILES_REVISION" ]]; then
  [[ "$DOTFILES_GIST" =~ ^https://gist\.github\.com/([a-zA-Z0-9-]+/)?[a-fA-F0-9]{20,64}/?$ && "$DOTFILES_REVISION" =~ ^[a-fA-F0-9]{40}$ ]] ||
    die 'Use --dotfiles-gist with a gist.github.com URL and --dotfiles-revision with a full 40-character SHA.'
fi

# Parse the entire list before CLT, Git repair, or Homebrew can make changes.
# shellcheck source=modules/taps.sh
source "$ROOT/modules/taps.sh"
load_custom_taps

[[ $(uname -s) == Darwin ]] || die 'Worker supports macOS only.'
[[ $DRY_RUN == 1 || $EUID != 0 ]] || die 'Run worker as your normal user, not with sudo.'
case "$WORKER_HOME" in /*) ;; *) die 'WORKER_HOME must be an absolute path.' ;; esac
case "$(uname -m)" in
  arm64) BREW_PREFIX=/opt/homebrew; WORKER_GOARCH=arm64 ;;
  x86_64)
    [[ $(sysctl -in sysctl.proc_translated 2>/dev/null || true) != 1 ]] || die 'Open a native terminal; this shell is running under Rosetta.'
    BREW_PREFIX=/usr/local; WORKER_GOARCH=amd64 ;;
  *) die 'Unsupported CPU architecture.' ;;
esac

[[ $DRY_RUN == 0 ]] || log 'DRY RUN: commands below are plans only; no external installers will run.'
for module in brew nvm go git zsh workflow agents desktop dotfiles vscode mac; do
  # shellcheck disable=SC1090
  source "$ROOT/modules/$module.sh"
  "setup_$module"
done

if [[ $DRY_RUN == 1 ]]; then
  log 'Dry run complete. Nothing was changed.'
else
  log 'Setup finished. Review any notices about preserved files or deferred steps above.'
  log 'Open a new terminal. Reopen Finder or log out to see preference changes.'
  log 'Sign in to GitHub and Docker as needed. Worker does not explicitly launch apps or start services; vendor installers may register background components.'
fi
