#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_workflow() {
  [[ $WITH_WORKFLOW == 1 ]] || return 0
  log 'Custom workflow tools and pinned Go helpers'
  local args=(--home "$WORKER_HOME" --root "$ROOT" --arch "$WORKER_GOARCH")
  [[ $REPLACE_CONFIG == 0 ]] || args+=(--replace-config)
  if [[ $DRY_RUN == 1 ]]; then
    log "  Would install ai-shot and ctx.sh as executables under $WORKER_HOME/bin/."
    log "  Would build missing Go helpers from $ROOT/extensions/go-workflow-tools.txt in temporary storage."
    log '  Would build ctx, gengql (upstream gql-gen), and g from pinned clean upstream revisions.'
    log '  Private ctx/gengql builds are deferred until gh auth login; local source changes are not included.'
    log '  Existing differing binaries are preserved unless --replace-config is selected.'
    return
  fi
  local status
  if run python3 "$ROOT/scripts/install-workflow.py" "${args[@]}"; then
    :
  else
    status=$?
    [[ $status == 2 ]] || return "$status"
    notice 'Some workflow tools were preserved or deferred; review the messages above and rerun after resolving them.'
  fi
}
