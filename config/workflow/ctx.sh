#!/usr/bin/env bash
set -euo pipefail

ctx_cli_bin=""

resolve_executable() {
  local candidate="$1"
  local resolved=""

  if [[ "${candidate}" == */* ]]; then
    [[ -f "${candidate}" && -x "${candidate}" ]] || return 1
    printf '%s\n' "${candidate}"
    return 0
  fi

  resolved="$(type -P -- "${candidate}" 2>/dev/null)" || return 1
  [[ -f "${resolved}" && -x "${resolved}" ]] || return 1
  printf '%s\n' "${resolved}"
}

warn_legacy_command() {
  local legacy="$1"
  local replacement="$2"
  local message="ctx.sh: legacy command \"${legacy}\" detected; native ctx CLI is active; forwarding to \"ctx ${replacement}\"."
  local lgr_bin=""

  if lgr_bin="$(resolve_executable lgr)" && LGR_NO_TIMESTAMP=true "${lgr_bin}" warn "${message}" >&2; then
    return 0
  fi
  printf 'warning: %s\n' "${message}" >&2
}

if [[ -n "${CTX_CLI_BIN:-}" ]] && ctx_cli_bin="$(resolve_executable "${CTX_CLI_BIN}")"; then
  :
elif [[ -f ./ctx && -x ./ctx ]]; then
  ctx_cli_bin="./ctx"
elif ctx_cli_bin="$(resolve_executable ctx)"; then
  :
else
  printf 'ctx.sh: unable to find an executable ctx binary; set CTX_CLI_BIN, place ./ctx in the current directory, or add ctx to PATH\n' >&2
  exit 127
fi

if [[ "${ctx_cli_bin}" -ef "$0" ]]; then
  printf 'ctx.sh: refusing to execute itself as the native ctx binary; fix CTX_CLI_BIN or PATH\n' >&2
  exit 126
fi

case "${1:-}" in
  status)
    shift
    warn_legacy_command status 'spec status'
    set -- spec status "$@"
    ;;
  run-all-phases)
    shift
    warn_legacy_command run-all-phases 'prompt run-all'
    native_args=()
    for arg in "$@"; do
      if [[ "${arg}" == '--claude' ]]; then
        native_args+=(--agent claude)
      else
        native_args+=("${arg}")
      fi
    done
    set -- prompt run-all "${native_args[@]}"
    ;;
esac

exec "${ctx_cli_bin}" "$@"
