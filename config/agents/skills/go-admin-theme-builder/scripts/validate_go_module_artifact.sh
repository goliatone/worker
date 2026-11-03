#!/bin/sh

# Download and test one exact published Go module in isolated caches.
# This is intentionally separate from the network-disabled repository audit.

set -eu

usage() {
  printf 'usage: %s [--require module@version]... module@version [test-pattern]...\n' \
    "${0##*/}" >&2
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

expected_requirements=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --require)
      [ "$#" -ge 2 ] || {
        usage
        exit 64
      }
      expected_requirements="${expected_requirements}${expected_requirements:+
}$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      usage
      exit 64
      ;;
    *)
      break
      ;;
  esac
done

[ "$#" -ge 1 ] || {
  usage
  exit 64
}

coordinate=$1
shift
module_path=${coordinate%@*}
module_version=${coordinate##*@}
[ "$module_path" != "$coordinate" ] &&
  [ -n "$module_path" ] &&
  [ -n "$module_version" ] ||
  die "module coordinate must be module@version: $coordinate"

command -v go >/dev/null 2>&1 || die "required tool not found: go"
command -v cp >/dev/null 2>&1 || die "required tool not found: cp"
command -v chmod >/dev/null 2>&1 || die "required tool not found: chmod"
command -v mktemp >/dev/null 2>&1 || die "required tool not found: mktemp"

artifact_base=${TMPDIR:-/tmp}
artifact_base=${artifact_base%/}
artifact_base=$(CDPATH='' cd "$artifact_base" 2>/dev/null && pwd -P) ||
  die "cannot resolve temporary directory: $artifact_base"
artifact_root=$(mktemp -d "$artifact_base/go-module-artifact.XXXXXX")

cleanup() {
  case "$artifact_root" in
    "$artifact_base"/go-module-artifact.*)
      if [ -d "$artifact_root" ]; then
        chmod -R u+w "$artifact_root"
        rm -r -- "$artifact_root"
      fi
      ;;
    *)
      printf 'refusing to remove unexpected artifact directory: %s\n' \
        "$artifact_root" >&2
      exit 1
      ;;
  esac
}
trap cleanup EXIT HUP INT TERM

artifact_modcache=$artifact_root/modcache
artifact_gocache=$artifact_root/gocache
artifact_gotmp=$artifact_root/gotmp
artifact_gopath=$artifact_root/gopath
artifact_source=$artifact_root/source
mkdir -p \
  "$artifact_modcache" \
  "$artifact_gocache" \
  "$artifact_gotmp" \
  "$artifact_gopath" \
  "$artifact_source"

artifact_go() {
  GOWORK=off \
    GOMODCACHE="$artifact_modcache" \
    GOCACHE="$artifact_gocache" \
    GOTMPDIR="$artifact_gotmp" \
    GOPATH="$artifact_gopath" \
    go "$@"
}

(
  CDPATH='' cd "$artifact_root" || exit "$?"
  artifact_go mod download "$coordinate"
)

artifact_record=$(
  CDPATH='' cd "$artifact_root" &&
    artifact_go list -m -f \
      '{{.Path}}|{{.Version}}|{{.Dir}}|{{if .Main}}true{{else}}false{{end}}|{{if .Replace}}{{.Replace.Path}}{{end}}' \
      "$coordinate"
)

old_ifs=$IFS
IFS='|'
read -r actual_path actual_version downloaded_dir is_main replacement <<EOF
$artifact_record
EOF
IFS=$old_ifs

[ "$actual_path" = "$module_path" ] ||
  die "downloaded module path $actual_path does not match $module_path"
[ "$actual_version" = "$module_version" ] ||
  die "downloaded version $actual_version does not match $module_version"
[ "$is_main" = false ] ||
  die "artifact validation resolved a local main module"
[ -z "$replacement" ] ||
  die "artifact validation resolved a replacement: $replacement"
case "$downloaded_dir" in
  "$artifact_modcache"/*) ;;
  *) die "artifact source is outside the isolated module cache: $downloaded_dir" ;;
esac
[ -f "$downloaded_dir/go.mod" ] ||
  die "downloaded artifact has no go.mod: $downloaded_dir"

cp -R "$downloaded_dir"/. "$artifact_source"
chmod -R u+w "$artifact_source"

active_replacements=$(
  CDPATH='' cd "$artifact_source" &&
    GOFLAGS=-mod=readonly artifact_go list -m -f \
      '{{if .Replace}}{{.Path}} => {{.Replace.Path}} {{.Replace.Version}}{{end}}' \
      all
)
[ -z "$active_replacements" ] ||
  die "artifact module graph contains a replacement: $active_replacements"

if [ -n "$expected_requirements" ]; then
  requirements_file=$artifact_root/requirements
  printf '%s\n' "$expected_requirements" >"$requirements_file"
  while IFS= read -r expected_coordinate; do
    [ -n "$expected_coordinate" ] || continue
    expected_path=${expected_coordinate%@*}
    expected_version=${expected_coordinate##*@}
    [ "$expected_path" != "$expected_coordinate" ] &&
      [ -n "$expected_path" ] &&
      [ -n "$expected_version" ] ||
      die "required coordinate must be module@version: $expected_coordinate"
    required_record=$(
      CDPATH='' cd "$artifact_source" &&
        GOFLAGS=-mod=readonly artifact_go list -m -f \
          '{{.Version}}|{{if .Replace}}{{.Replace.Path}}{{end}}' \
          "$expected_path"
    )
    old_ifs=$IFS
    IFS='|'
    read -r required_version required_replacement <<EOF
$required_record
EOF
    IFS=$old_ifs
    [ "$required_version" = "$expected_version" ] ||
      die "$module_path requires $expected_path $required_version, expected $expected_version"
    [ -z "$required_replacement" ] ||
      die "$module_path resolves a replacement for $expected_path: $required_replacement"
  done <"$requirements_file"
fi

if [ "$#" -eq 0 ]; then
  set -- ./...
fi

(
  CDPATH='' cd "$artifact_source" || exit "$?"
  GOFLAGS=-mod=readonly artifact_go test "$@"
)

printf 'artifact module: %s\n' "$actual_path"
printf 'artifact version: %s\n' "$actual_version"
printf 'artifact source: isolated module cache\n'
printf 'artifact replacement: none\n'
printf 'artifact tests: passed\n'
