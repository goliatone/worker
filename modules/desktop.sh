#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_desktop() {
  [[ $WITH_DESKTOP == 1 ]] || return 0
  log 'iTerm2 portable appearance profile'
  local args=(--home "$WORKER_HOME" --source "$ROOT/config/iterm/worker.json"
    --destination 'Library/Application Support/iTerm2/DynamicProfiles/worker.json')
  [[ -f "$ROOT/config/iterm/worker.json" ]] || die 'Missing iTerm profile source.'
  [[ $REPLACE_CONFIG == 0 ]] || args+=(--replace-config)
  run python3 "$ROOT/scripts/worker_files.py" "${args[@]}"
  log '  Choose the Worker profile in iTerm2. Existing profiles and the default-profile selection are preserved.'
}
