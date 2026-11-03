#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_desktop() {
  [[ $WITH_DESKTOP == 1 ]] || return 0
  log 'iTerm2 portable appearance profile'
  install_file "$ROOT/config/iterm/worker.json" "$WORKER_HOME/Library/Application Support/iTerm2/DynamicProfiles/worker.json"
  log '  Choose the Worker profile in iTerm2. Existing profiles and the default-profile selection are preserved.'
}
