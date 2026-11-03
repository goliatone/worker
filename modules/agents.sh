#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_agents() {
  [[ $WITH_AGENTS == 1 ]] || return 0
  log 'Coding-agent configuration and captured skills'
  if [[ $DRY_RUN == 1 ]]; then
    log "  Would install portable Codex/Claude/Cursor settings and selected skills under $WORKER_HOME."
    log '  Existing settings/skills are preserved unless --replace-config is selected.'
    return
  fi
  local args=(--home "$WORKER_HOME" --root "$ROOT")
  [[ $REPLACE_CONFIG == 0 ]] || args+=(--replace-config)
  run python3 "$ROOT/scripts/install-agents.py" "${args[@]}"
  log '  Sign in to codex, claude, and cursor-agent when ready. Account tokens, project trust, plugins, hooks, and MCP connections are not copied.'
}
