#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_brew() {
  local installer installed_prefix
  log 'Homebrew and core packages'
  if [[ $DRY_RUN == 1 ]]; then
    log '  Would verify Xcode Command Line Tools; if absent, request installation and stop for completion.'
  elif ! xcode-select -p >/dev/null 2>&1; then
    run xcode-select --install
    die 'Complete the Command Line Tools installation, then rerun ./make.'
  fi

  BREW_BIN=$(command -v brew || true)
  if [[ -z "$BREW_BIN" && -x "$BREW_PREFIX/bin/brew" ]]; then BREW_BIN="$BREW_PREFIX/bin/brew"; fi
  if [[ -z "$BREW_BIN" ]]; then
    BREW_BIN="$BREW_PREFIX/bin/brew"
    if [[ $DRY_RUN == 1 ]]; then
      log '  Would download https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh and run it with /bin/bash.'
    else
      installer=$(mktemp -t worker-homebrew)
      if ! curl --fail --show-error --silent --location https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"; then
        rm -f "$installer"
        die 'Homebrew installer download failed.'
      fi
      if ! /bin/bash "$installer"; then
        rm -f "$installer"
        die 'Homebrew installation failed.'
      fi
      rm -f "$installer"
      [[ -x "$BREW_BIN" ]] || die "Homebrew was not installed at $BREW_BIN."
    fi
  fi
  if [[ $DRY_RUN == 0 ]]; then
    installed_prefix=$("$BREW_BIN" --prefix)
    if [[ "$BREW_PREFIX" == /opt/homebrew && "$installed_prefix" == /usr/local ]] ||
       [[ "$BREW_PREFIX" == /usr/local && "$installed_prefix" == /opt/homebrew ]]; then
      die "Homebrew at $installed_prefix does not match this shell's architecture; use the native installation at $BREW_PREFIX."
    fi
    BREW_PREFIX=$installed_prefix
    export PATH="$BREW_PREFIX/bin:$BREW_PREFIX/sbin:$PATH"
  fi
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ANALYTICS=1
  run "$BREW_BIN" analytics off
  run "$BREW_BIN" bundle install --no-upgrade --file="$ROOT/extensions/Brewfile"
}
