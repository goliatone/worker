#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_zsh() {
  log 'Zsh configuration'
  clone_public_repo https://github.com/ohmyzsh/ohmyzsh.git b509b1c6ed0c1ba37de12cbd37f30b2b2f61193a "$WORKER_HOME/.oh-my-zsh" oh-my-zsh.sh
  clone_public_repo https://github.com/larkery/zsh-histdb.git 30797f0c50c31c8d8de32386970c5d480e5ab35d "$WORKER_HOME/.oh-my-zsh/custom/plugins/zsh-histdb" sqlite-history.zsh "$ROOT/config/zsh/zsh-histdb.patch"
  local name
  for name in zshenv zprofile zshrc; do
    install_file "$ROOT/config/zsh/$name" "$WORKER_HOME/.$name"
  done
  install_file "$ROOT/config/zsh/pandoc-mdfmt.yaml" "$WORKER_HOME/.config/pandoc-mdfmt.yaml"
}
