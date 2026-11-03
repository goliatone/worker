#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_vscode() {
  local user_dir source_file cli installed extension channel failures
  log 'VS Code Insiders configuration'
  user_dir="$WORKER_HOME/Library/Application Support/Code - Insiders/User"
  install_file "$ROOT/config/vscode/settings.json" "$user_dir/settings.json"
  install_file "$ROOT/config/vscode/keybindings.json" "$user_dir/keybindings.json"
  for source_file in "$ROOT/config/vscode/snippets/"*; do
    [[ -f "$source_file" ]] || continue
    install_file "$source_file" "$user_dir/snippets/$(basename "$source_file")"
  done
  if [[ $SKIP_EXTENSIONS == 1 ]]; then log '  Extension installation skipped.'; return; fi
  cli=code-insiders
  installed=''
  if [[ $DRY_RUN == 0 ]]; then
    cli=$(command -v code-insiders || true)
    [[ -n "$cli" ]] || die 'code-insiders is missing after Homebrew setup.'
    installed=$("$cli" --list-extensions)
  fi
  failures=0
  while read -r extension channel || [[ -n "${extension:-}" ]]; do
    [[ -n "$extension" && "$extension" != \#* ]] || continue
    if printf '%s\n' "$installed" | grep -Fxi -- "$extension" >/dev/null; then
      log "  Keep installed extension: $extension"
    elif [[ "$channel" == prerelease ]]; then
      run "$cli" --install-extension "$extension" --pre-release </dev/null || failures=$((failures + 1))
    else
      run "$cli" --install-extension "$extension" </dev/null || failures=$((failures + 1))
    fi
  done < "$ROOT/extensions/vscode-insiders.txt"
  [[ $failures == 0 ]] || die "$failures extension installations failed. Review the errors, update the manifest if retired, and rerun."
}
