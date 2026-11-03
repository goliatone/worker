#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

set_preference() {
  local domain=$1 key=$2 type=$3 value=$4 current
  if [[ $DRY_RUN == 0 ]]; then
    current=$(defaults read "$domain" "$key" 2>/dev/null || true)
    [[ "$type" != -bool ]] || { case "$current" in true|YES) current=1 ;; false|NO) current=0 ;; esac; }
    if [[ "$current" == "$value" ]]; then log "  Unchanged: $domain $key"; return; fi
  fi
  run defaults write "$domain" "$key" "$type" "$value"
}

setup_mac() {
  if [[ $SKIP_MACOS == 1 ]]; then log 'macOS preferences skipped.'; return; fi
  log 'Finder and Dock preferences'
  set_preference com.apple.finder AppleShowAllFiles -bool 1
  set_preference NSGlobalDomain AppleShowAllExtensions -bool 1
  set_preference com.apple.finder FXPreferredViewStyle -string clmv
  set_preference com.apple.finder ShowStatusBar -bool 1
  set_preference com.apple.dock autohide -bool 1
}
