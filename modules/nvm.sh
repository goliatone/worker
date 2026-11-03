#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_nvm() {
  local node_default installed_node node_version pnpm_version
  log 'Node through NVM, with pnpm'
  export NVM_DIR="$WORKER_HOME/.nvm"
  clone_public_repo https://github.com/nvm-sh/nvm.git v0.40.8 "$NVM_DIR" nvm.sh
  if [[ $DRY_RUN == 1 ]]; then
    log '  Would load NVM, keep a default Node >=18.12, or install the current LTS when no default exists.'
    log '  Would install pnpm@10.32.1 only if pnpm is absent from the selected Node installation.'
    return
  fi
  # NVM does not support errexit/nounset. Check each result explicitly here.
  set +eu
  # shellcheck disable=SC1091
  source "$NVM_DIR/nvm.sh" --no-use || die 'Could not load NVM.'
  node_default=$(nvm version default || true)
  if [[ -z "$node_default" || "$node_default" == N/A || "$node_default" == system ]]; then
    nvm install --lts || die 'Could not install Node LTS.'
    installed_node=$(nvm current) || die 'Could not determine the installed Node version.'
    nvm alias default "$installed_node" || die 'Could not set the default Node version.'
  else
    nvm use default || die 'Could not activate the existing default Node version.'
  fi
  set -eu
  node_version=$(node --version)
  [[ "$node_version" =~ ^v([0-9]+)\.([0-9]+)\. ]] || die "Could not parse the selected Node version: $node_version"
  if (( BASH_REMATCH[1] < 18 || (BASH_REMATCH[1] == 18 && BASH_REMATCH[2] < 12) )); then
    die "pnpm 10 requires Node >=18.12; the selected default is $node_version. Run nvm install --lts and nvm alias default 'lts/*', then rerun worker."
  fi
  pnpm_version=$(npm list --global --depth=0 pnpm --json 2>/dev/null || true)
  if printf '%s' "$pnpm_version" | node -e 'let s=""; process.stdin.on("data",d=>s+=d); process.stdin.on("end",()=>{try{process.exit(JSON.parse(s).dependencies?.pnpm?.version ? 0 : 1)}catch{process.exit(1)}})'; then
    log '  pnpm already installed for the selected Node.'
  else
    run npm install --global pnpm@10.32.1
  fi
}
