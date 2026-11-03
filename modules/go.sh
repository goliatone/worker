#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

setup_go() {
  local binary package version metadata
  log 'Go development tools'
  while read -r binary package || [[ -n "${binary:-}" ]]; do
    [[ -n "$binary" && "$binary" != \#* ]] || continue
    version=${package##*@}
    if [[ $DRY_RUN == 0 && -x "$WORKER_HOME/go/bin/$binary" ]]; then
      metadata=$(go version -m "$WORKER_HOME/go/bin/$binary" </dev/null 2>/dev/null || true)
      if printf '%s\n' "$metadata" | awk -v v="$version" -v p="${package%@*}" -v a="$WORKER_GOARCH" '
        $1 == "path" && $2 == p { path=1 }
        $1 == "mod" && $3 == v { version=1 }
        $1 == "build" && $2 == "GOOS=darwin" { os=1 }
        $1 == "build" && $2 == "GOARCH=" a { arch=1 }
        END { exit !(path && version && os && arch) }'; then
        log "  Already installed: $binary@$version"
        continue
      fi
    fi
    # Do not inherit a caller's cross-compilation target or the manifest's stdin.
    run env GOBIN="$WORKER_HOME/go/bin" GOOS=darwin GOARCH="$WORKER_GOARCH" go install "$package" </dev/null
  done < "$ROOT/extensions/go-tools.txt"
}
