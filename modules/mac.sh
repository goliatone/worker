#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

normalize_preference_bool() {
  case "$1" in
    1|[Tt][Rr][Uu][Ee]|[Yy][Ee][Ss]) printf 'true\n' ;;
    0|[Ff][Aa][Ll][Ss][Ee]|[Nn][Oo]) printf 'false\n' ;;
    *) return 1 ;;
  esac
}

set_preference() {
  local domain=$1 key=$2 type=$3 value=$4 current
  # defaults writes require words, while reads return numeric 1/0 on macOS.
  if [[ "$type" == -bool ]]; then
    value=$(normalize_preference_bool "$value") || die "Invalid boolean preference: $domain $key."
  fi
  if [[ $DRY_RUN == 0 ]]; then
    current=$(defaults read "$domain" "$key" 2>/dev/null || true)
    if [[ "$type" == -bool ]]; then current=$(normalize_preference_bool "$current" || true); fi
    if [[ "$current" == "$value" ]]; then log "  Unchanged: $domain $key"; return; fi
  fi
  run defaults write "$domain" "$key" "$type" "$value" ||
    die "Could not set macOS preference: $domain $key. Resolve the defaults error and rerun."
}

setup_mac() {
  if [[ $SKIP_MACOS == 1 ]]; then log 'macOS preferences skipped.'; return; fi
  log 'Finder and Dock preferences'
  set_preference com.apple.finder AppleShowAllFiles -bool true
  set_preference NSGlobalDomain AppleShowAllExtensions -bool true
  set_preference com.apple.finder FXPreferredViewStyle -string clmv
  set_preference com.apple.finder ShowStatusBar -bool true
  set_preference com.apple.dock autohide -bool true
}
