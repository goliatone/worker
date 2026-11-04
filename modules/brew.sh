#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_brew() {
  local installer installed_prefix manifest macos_version macos_major
  local bundle selected
  local manifests=("$ROOT/extensions/Brewfile")
  if [[ ${WITH_DESKFLOW:-0} == 1 ]]; then
    manifests+=("$ROOT/extensions/Brewfile.deskflow")
  fi
  if [[ ${WITH_AI:-0} == 1 ]]; then
    manifests+=("$ROOT/extensions/Brewfile.ai")
  fi
  for bundle in workflow agents backend access desktop; do
    selected=WITH_$(printf '%s' "$bundle" | tr '[:lower:]' '[:upper:]')
    if [[ ${!selected:-0} == 1 ]]; then manifests+=("$ROOT/extensions/Brewfile.$bundle"); fi
  done
  for manifest in "${manifests[@]}"; do
    [[ -f "$manifest" && -r "$manifest" ]] || die "Missing or unreadable Brewfile: $manifest"
  done
  if [[ ${WITH_AI:-0} == 1 ]]; then
    [[ $WORKER_GOARCH == arm64 ]] || die '--with-ai requires Apple Silicon; the LM Studio, Bionic, and Unsloth casks do not support Intel Macs.'
    macos_version=$(sw_vers -productVersion)
    macos_major=${macos_version%%.*}
    case "$macos_major" in
      ''|*[!0-9]*) die "Could not determine the macOS version: $macos_version" ;;
    esac
    [[ $macos_major -ge 14 ]] || die "--with-ai requires macOS 14 or later (Ollama requirement); found $macos_version."
  fi
  if [[ ${WITH_DESKTOP:-0} == 1 || ${WITH_ACCESS:-0} == 1 ]]; then
    macos_version=$(sw_vers -productVersion)
    macos_major=${macos_version%%.*}
    case "$macos_major" in ''|*[!0-9]*) die "Could not determine the macOS version: $macos_version" ;; esac
    if [[ ${WITH_DESKTOP:-0} == 1 ]]; then
      [[ $macos_major -ge 14 ]] || die '--with-desktop requires macOS 14 or later.'
    else
      [[ $macos_major -ge 13 ]] || die '--with-access requires macOS 13 or later.'
    fi
  fi
  if [[ ${WITH_WORKFLOW:-0} == 1 ]]; then
    [[ -r "$ROOT/extensions/go-workflow-tools.txt" ]] || die 'Missing Go workflow tool manifest.'
    [[ -r "$ROOT/extensions/custom-workflow-tools.json" ]] || die 'Missing custom workflow tool manifest.'
  fi
  if [[ ${WITH_AGENTS:-0} == 1 ]]; then
    [[ -r "$ROOT/extensions/agent-files.json" ]] || die 'Missing agent file manifest.'
  fi
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
  setup_custom_taps
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
  if [[ ${WITH_AI:-0} == 1 ]]; then
    log 'Optional AI apps: Ollama (app and CLI), LM Studio, LM Studio Bionic, and Unsloth Desktop.'
    run "$BREW_BIN" bundle install --no-upgrade --file="$ROOT/extensions/Brewfile.ai"
    log '  Open the apps when ready to complete first-run setup and select models. Worker does not launch them or download models.'
  fi
  for bundle in workflow agents backend access desktop; do
    selected=WITH_$(printf '%s' "$bundle" | tr '[:lower:]' '[:upper:]')
    if [[ ${!selected:-0} == 1 ]]; then
      log "Optional bundle: $bundle"
      run "$BREW_BIN" bundle install --no-upgrade --file="$ROOT/extensions/Brewfile.$bundle"
    fi
  done
  if [[ ${WITH_BACKEND:-0} == 1 ]]; then
    log '  Services are not started. PostgreSQL may create its initial empty cluster during package installation; existing data is not migrated.'
    log '  Run mkcert -install and sign in to LocalStack/ngrok only when needed. No trust roots or tunnels are configured by worker.'
  fi
  if [[ ${WITH_ACCESS:-0} == 1 ]]; then
    log '  Complete 1Password and Tailscale sign-in and permissions manually. Vendor package installers may register background components.'
  fi

}
