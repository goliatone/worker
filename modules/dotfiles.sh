#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_dotfiles() {
  [[ -n "$DOTFILES_GIST" ]] || return 0
  log "Shared dotfiles: $DOTFILES_GIST at $DOTFILES_REVISION"
  if [[ $DRY_RUN == 1 ]]; then
    log "  Would fetch zshrc.shared, gitconfig.shared, and optional zshrc.shared.pre into temporary storage."
    log "  Would validate syntax and install under $WORKER_HOME/.config/worker/."
    log '  Would back up and migrate recognized Git/Zsh include hooks, leaving local overrides last.'
    log '  No remote contents or hook layouts have been validated in this dry run.'
    [[ $REPLACE_CONFIG == 0 ]] || log '  Would back up and replace differing shared files.'
    return
  fi
  local args=(--home "$WORKER_HOME" --gist "$DOTFILES_GIST" --revision "$DOTFILES_REVISION")
  [[ $REPLACE_CONFIG == 0 ]] || args+=(--replace-config)
  run python3 "$ROOT/scripts/dotfiles.py" "${args[@]}"
}
