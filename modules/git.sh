#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_git() {
  log 'Git configuration and GitHub CLI extension'
  install_file "$ROOT/config/git/gitconfig" "$WORKER_HOME/.gitconfig"
  install_file "$ROOT/config/git/ignore" "$WORKER_HOME/.gitignore_global"
  install_file "$ROOT/config/gh-dash/config.yml" "$WORKER_HOME/.config/gh-dash/config.yml"
  if [[ $DRY_RUN == 1 ]]; then
    log '  Would install dlvhdr/gh-dash if missing and GitHub CLI is authenticated; otherwise report the sign-in step.'
  elif ! gh auth status >/dev/null 2>&1; then
    notice 'gh-dash deferred: run gh auth login, then rerun ./make.'
  else
    local extensions
    extensions=$(gh extension list)
    if [[ "$extensions" == *dlvhdr/gh-dash* || "$extensions" == *gh-dash/gh-dash* ]]; then
      log '  gh-dash already installed.'
    else
      run gh extension install dlvhdr/gh-dash
    fi
  fi
}
