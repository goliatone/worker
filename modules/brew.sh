#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_brew() {
  local installer installed_prefix manifest
  local manifests=("$ROOT/extensions/Brewfile")
  if [[ ${WITH_DESKFLOW:-0} == 1 ]]; then
    manifests+=("$ROOT/extensions/Brewfile.deskflow")
  fi
  for manifest in "${manifests[@]}"; do
    [[ -f "$manifest" && -r "$manifest" ]] || die "Missing or unreadable Brewfile: $manifest"
  done
  log 'Homebrew and core packages'
  if [[ $DRY_RUN == 1 ]]; then
    log '  Would verify Xcode Command Line Tools; if absent, request installation and stop for completion.'
  elif ! xcode-select -p >/dev/null 2>&1; then
    run xcode-select --install
    die 'Complete the Command Line Tools installation, then rerun ./make.'
  fi
  repair_legacy_git_rewrite

  BREW_BIN=$(command -v brew || true)
  if [[ -z "$BREW_BIN" && -x "$BREW_PREFIX/bin/brew" ]]; then BREW_BIN="$BREW_PREFIX/bin/brew"; fi
  if [[ -z "$BREW_BIN" ]]; then
    BREW_BIN="$BREW_PREFIX/bin/brew"
    if [[ $DRY_RUN == 1 ]]; then
      log '  Would download https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh and run it with /bin/bash, ignoring global/system Git configuration.'
    else
      installer=$(mktemp -t worker-homebrew)
      if ! curl --fail --show-error --silent --location https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"; then
        rm -f "$installer"
        die 'Homebrew installer download failed.'
      fi
      if ! env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 /bin/bash "$installer"; then
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
  # Bundle cleanup is separate from install cleanup and can remove unrelated
  # packages/trust entries, especially with the separate optional Brewfile.
  unset HOMEBREW_BUNDLE_INSTALL_CLEANUP HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP
  run "$BREW_BIN" analytics off
  log '  Includes Amphetamine (Mac App Store, 937984704); sign in to the App Store before its first install.'
  log '  App Store installation may request authentication. If it fails, finish signing in and rerun ./make.'
  # The legacy URL rewrite was repaired above, before any Homebrew commands.
  run "$BREW_BIN" bundle install --no-upgrade --file="$ROOT/extensions/Brewfile"
  if [[ ${WITH_DESKFLOW:-0} == 1 ]]; then
    log 'Optional Deskflow: stable release from deskflow/tap; trust only its deskflow cask.'
    run "$BREW_BIN" bundle install --no-upgrade --file="$ROOT/extensions/Brewfile.deskflow"
    log '  Open Deskflow on both Macs to pair them and grant Accessibility and Local Network permissions.'
  fi
}
