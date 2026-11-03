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
WORKER_HOME=${WORKER_HOME:-$HOME}
WARNINGS=0

usage() {
  cat <<'EOF'
Usage: ./make [--dry-run] [--replace-config] [--skip-macos] [--skip-extensions] [--with-deskflow]

  --dry-run         Print the plan. No downloads, installs, config writes or defaults changes.
  --replace-config  Back up and replace differing config files (default: preserve them).
  --skip-macos      Leave macOS preferences alone.
  --skip-extensions Install Insiders configuration without installing extensions.
  --with-deskflow    Also install Deskflow for sharing a keyboard and mouse between computers.
  --help            Show this help.

Run as your normal user. Homebrew may request administrator access when needed.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --replace-config) REPLACE_CONFIG=1 ;;
    --skip-macos) SKIP_MACOS=1 ;;
    --skip-extensions) SKIP_EXTENSIONS=1 ;;
    --with-deskflow) WITH_DESKFLOW=1 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done

# All modules share one environment; none source the user's shell configuration.
WORKER_LOADED=1
# shellcheck source=utils.sh
source "$ROOT/utils.sh"
trap 'printf "Worker stopped at %s:%s. Resolve the error and rerun.\n" "${BASH_SOURCE[0]}" "$LINENO" >&2' ERR

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
for module in brew nvm go git zsh vscode mac; do
  # shellcheck disable=SC1090
  source "$ROOT/modules/$module.sh"
  "setup_$module"
done

if [[ $DRY_RUN == 1 ]]; then
  log "Dry run complete ($WARNINGS notices). Nothing was changed."
else
  log "Setup finished ($WARNINGS notices; review any preserved files or deferred steps above)."
  log 'Open a new terminal. Reopen Finder or log out to see preference changes.'
  log 'Sign in to GitHub and Docker as needed; no apps or background services were launched.'
fi
