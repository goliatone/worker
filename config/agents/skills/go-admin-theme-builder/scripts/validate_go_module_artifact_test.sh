#!/bin/sh

set -eu

script_dir=$(CDPATH='' cd "${0%/*}" 2>/dev/null && pwd -P)
validator=$script_dir/validate_go_module_artifact.sh
test_base=${TMPDIR:-/tmp}
test_base=${test_base%/}
test_base=$(CDPATH='' cd "$test_base" 2>/dev/null && pwd -P)
test_root=$(mktemp -d "$test_base/go-module-artifact-test.XXXXXX")

cleanup() {
  case "$test_root" in
    "$test_base"/go-module-artifact-test.*)
      if [ -d "$test_root" ]; then
        chmod -R u+w "$test_root"
        rm -r -- "$test_root"
      fi
      ;;
    *)
      printf 'refusing to remove unexpected test directory: %s\n' "$test_root" >&2
      exit 1
      ;;
  esac
}
trap cleanup EXIT HUP INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

command -v zip >/dev/null 2>&1 || fail "required test tool not found: zip"

proxy_root=$test_root/proxy
build_root=$test_root/build
dependency_path=example.com/artifact-dependency
dependency_version=v1.0.0
artifact_path=example.com/theme-artifact
artifact_version=v1.0.0
dependency_dir=$build_root/$dependency_path@$dependency_version
artifact_dir=$build_root/$artifact_path@$artifact_version

mkdir -p \
  "$proxy_root/$dependency_path/@v" \
  "$proxy_root/$artifact_path/@v" \
  "$dependency_dir" \
  "$artifact_dir"

cat >"$dependency_dir/go.mod" <<EOF
module $dependency_path

go 1.22
EOF
cat >"$dependency_dir/dependency.go" <<'EOF'
package dependency

func Value() string { return "dependency" }
EOF

cat >"$artifact_dir/go.mod" <<EOF
module $artifact_path

go 1.22

require $dependency_path $dependency_version
EOF
cat >"$artifact_dir/artifact.go" <<EOF
package artifact

import dependency "$dependency_path"

func Value() string { return dependency.Value() }
EOF
cat >"$artifact_dir/artifact_test.go" <<'EOF'
package artifact

import "testing"

func TestValue(t *testing.T) {
	if Value() != "dependency" {
		t.Fatalf("unexpected value %q", Value())
	}
}
EOF

cat >"$proxy_root/$dependency_path/@v/$dependency_version.mod" <<EOF
module $dependency_path

go 1.22
EOF
cat >"$proxy_root/$dependency_path/@v/$dependency_version.info" <<EOF
{"Version":"$dependency_version","Time":"2026-07-28T00:00:00Z"}
EOF
printf '%s\n' "$dependency_version" \
  >"$proxy_root/$dependency_path/@v/list"
(
  CDPATH='' cd "$build_root" || exit "$?"
  zip -q -r \
    "$proxy_root/$dependency_path/@v/$dependency_version.zip" \
    "$dependency_path@$dependency_version"
)

(
  CDPATH='' cd "$artifact_dir" || exit "$?"
  GOWORK=off \
    GOPROXY="file://$proxy_root" \
    GOSUMDB=off \
    go mod tidy
)

cp "$artifact_dir/go.mod" \
  "$proxy_root/$artifact_path/@v/$artifact_version.mod"
cat >"$proxy_root/$artifact_path/@v/$artifact_version.info" <<EOF
{"Version":"$artifact_version","Time":"2026-07-28T00:00:00Z"}
EOF
printf '%s\n' "$artifact_version" \
  >"$proxy_root/$artifact_path/@v/list"
(
  CDPATH='' cd "$build_root" || exit "$?"
  zip -q -r \
    "$proxy_root/$artifact_path/@v/$artifact_version.zip" \
    "$artifact_path@$artifact_version"
)

output=$(
  GOPROXY="file://$proxy_root" GOSUMDB=off \
    "$validator" \
      --require "$dependency_path@$dependency_version" \
      "$artifact_path@$artifact_version"
)
printf '%s\n' "$output" | grep -F "artifact module: $artifact_path" >/dev/null ||
  fail "artifact module was not reported"
printf '%s\n' "$output" | grep -F "artifact version: $artifact_version" >/dev/null ||
  fail "artifact version was not reported"
printf '%s\n' "$output" | grep -F "artifact tests: passed" >/dev/null ||
  fail "artifact test result was not reported"

set +e
wrong_requirement_output=$(
  GOPROXY="file://$proxy_root" GOSUMDB=off \
    "$validator" \
      --require "$dependency_path@v1.1.0" \
      "$artifact_path@$artifact_version" 2>&1
)
wrong_requirement_exit=$?
set -e
[ "$wrong_requirement_exit" -ne 0 ] ||
  fail "wrong dependency requirement unexpectedly passed"
printf '%s\n' "$wrong_requirement_output" |
  grep -F "expected v1.1.0" >/dev/null ||
  fail "wrong dependency diagnostic was not reported"

replacement_version=v1.0.1
dependency_replacement_version=v1.0.1
dependency_replacement_dir=$build_root/$dependency_path@$dependency_replacement_version
cp -R "$dependency_dir" "$dependency_replacement_dir"
cp "$dependency_replacement_dir/go.mod" \
  "$proxy_root/$dependency_path/@v/$dependency_replacement_version.mod"
cat >"$proxy_root/$dependency_path/@v/$dependency_replacement_version.info" <<EOF
{"Version":"$dependency_replacement_version","Time":"2026-07-28T01:00:00Z"}
EOF
printf '%s\n%s\n' "$dependency_version" "$dependency_replacement_version" \
  >"$proxy_root/$dependency_path/@v/list"
(
  CDPATH='' cd "$build_root" || exit "$?"
  zip -q -r \
    "$proxy_root/$dependency_path/@v/$dependency_replacement_version.zip" \
    "$dependency_path@$dependency_replacement_version"
)
cat >>"$artifact_dir/go.mod" <<EOF

replace $dependency_path $dependency_version => $dependency_path $dependency_replacement_version
EOF
(
  CDPATH='' cd "$artifact_dir" || exit "$?"
  GOWORK=off \
    GOPROXY="file://$proxy_root" \
    GOSUMDB=off \
    go mod tidy
)
replacement_dir=$build_root/$artifact_path@$replacement_version
cp -R "$artifact_dir" "$replacement_dir"
cp "$artifact_dir/go.mod" \
  "$proxy_root/$artifact_path/@v/$replacement_version.mod"
cat >"$proxy_root/$artifact_path/@v/$replacement_version.info" <<EOF
{"Version":"$replacement_version","Time":"2026-07-28T01:00:00Z"}
EOF
printf '%s\n%s\n' "$artifact_version" "$replacement_version" \
  >"$proxy_root/$artifact_path/@v/list"
(
  CDPATH='' cd "$build_root" || exit "$?"
  zip -q -r \
    "$proxy_root/$artifact_path/@v/$replacement_version.zip" \
    "$artifact_path@$replacement_version"
)

set +e
replacement_output=$(
  GOPROXY="file://$proxy_root" GOSUMDB=off \
    "$validator" "$artifact_path@$replacement_version" 2>&1
)
replacement_exit=$?
set -e
[ "$replacement_exit" -ne 0 ] ||
  fail "artifact replacement unexpectedly passed"
printf '%s\n' "$replacement_output" |
  grep -F "module graph contains a replacement" >/dev/null ||
  fail "artifact replacement diagnostic was not reported"

printf 'validate_go_module_artifact tests passed\n'
