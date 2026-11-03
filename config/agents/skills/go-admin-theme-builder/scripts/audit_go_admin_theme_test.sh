#!/bin/sh

set -eu

script_dir=$(CDPATH='' cd "${0%/*}" 2>/dev/null && pwd -P)
audit_script=$script_dir/audit_go_admin_theme.sh
repo_root=$(CDPATH='' cd "$script_dir/../../../.." 2>/dev/null && pwd -P)
test_base=${TMPDIR:-/tmp}
test_base=${test_base%/}
test_base=$(CDPATH='' cd "$test_base" 2>/dev/null && pwd -P)
test_root=$(mktemp -d "$test_base/go-admin-theme-audit-test.XXXXXX")

cleanup() {
  case "$test_root" in
    "$test_base"/go-admin-theme-audit-test.*)
      [ ! -d "$test_root" ] || rm -r "$test_root"
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

assert_contains() {
  output=$1
  expected=$2
  printf '%s\n' "$output" | grep -F "$expected" >/dev/null ||
    fail "missing expected output: $expected"
}

assert_not_contains() {
  output=$1
  unexpected=$2
  if printf '%s\n' "$output" | grep -F "$unexpected" >/dev/null; then
    fail "unexpected output: $unexpected"
  fi
}

root_output=$(GOWORK=off "$audit_script" "$repo_root")
assert_contains "$root_output" "dependency: github.com/goliatone/go-admin/quickstart"
assert_contains "$root_output" "  source-state: local-nested"
assert_contains "$root_output" "  source-module: github.com/goliatone/go-admin/quickstart"
assert_contains "$root_output" "    view_engine.go"
assert_contains "$root_output" "    static_assets.go"
assert_contains "$root_output" "    static_assets_test.go"

fixture_root=$test_root/fixture
workspace_root="$test_root/workspace with spaces"
module_root=$workspace_root/modules
cache_root=$test_root/cache
mkdir -p "$fixture_root" "$module_root" "$cache_root"

cat >"$fixture_root/go.mod" <<'EOF'
module example.com/theme-host

go 1.22

require (
	github.com/goliatone/go-admin v9.9.9
	github.com/goliatone/go-admin/quickstart v9.9.9
	github.com/goliatone/go-theme v9.9.9
	github.com/goliatone/go-formgen v9.9.9
	github.com/goliatone/go-dashboard v9.9.9
)
EOF

auto_workspace_root=$test_root/auto-workspace
auto_fixture_root=$auto_workspace_root/fixture
mkdir -p "$auto_fixture_root"
cat >"$auto_fixture_root/go.mod" <<'EOF'
module example.com/auto-theme-host

go 1.22
EOF
cat >"$auto_workspace_root/go.work" <<'EOF'
go 1.22

use ./fixture
EOF

auto_workspace_output=$(
  GOWORK=auto GOMODCACHE="$cache_root" GOPROXY=off GOSUMDB=off \
    "$audit_script" "$auto_fixture_root"
)
assert_contains "$auto_workspace_output" "workspace: $auto_workspace_root/go.work"

empty_workspace_output=$(
  GOWORK='' GOMODCACHE="$cache_root" GOPROXY=off GOSUMDB=off \
    "$audit_script" "$auto_fixture_root"
)
assert_contains "$empty_workspace_output" "workspace: $auto_workspace_root/go.work"

unset_workspace_output=$(
  unset GOWORK
  GOMODCACHE="$cache_root" GOPROXY=off GOSUMDB=off \
    "$audit_script" "$auto_fixture_root"
)
assert_contains "$unset_workspace_output" "workspace: $auto_workspace_root/go.work"

disabled_workspace_output=$(
  GOWORK=off GOMODCACHE="$cache_root" GOPROXY=off GOSUMDB=off \
    "$audit_script" "$auto_fixture_root"
)
assert_contains "$disabled_workspace_output" "workspace: none"
assert_not_contains "$disabled_workspace_output" \
  "workspace: $auto_workspace_root/go.work"

for module_name in go-admin go-admin-quickstart go-theme go-formgen; do
  mkdir -p "$module_root/$module_name"
done
mkdir -p "$module_root/go dashboard"

cat >"$module_root/go-admin/go.mod" <<'EOF'
module github.com/goliatone/go-admin

go 1.22
EOF
cat >"$module_root/go-admin-quickstart/go.mod" <<'EOF'
module github.com/goliatone/go-admin/quickstart

go 1.22
EOF
cat >"$module_root/go-theme/go.mod" <<'EOF'
module github.com/goliatone/go-theme

go 1.22
EOF
cat >"$module_root/go-formgen/go.mod" <<'EOF'
module github.com/goliatone/go-formgen

go 1.22
EOF
cat >"$module_root/go dashboard/go.mod" <<'EOF'
module github.com/goliatone/go-dashboard

go 1.22
EOF

cat >"$workspace_root/go.work" <<EOF
go 1.22

use (
	"./modules/go-admin"
	"./modules/go-admin-quickstart"
	"./modules/go-theme"
	"./modules/go-formgen"
)

replace github.com/goliatone/go-dashboard => "./modules/go dashboard"
EOF

before_cache=$(find "$cache_root" -mindepth 1 -print | LC_ALL=C sort)
workspace_output=$(
  GOWORK="$workspace_root/go.work" GOMODCACHE="$cache_root" GOPROXY=off \
    GOSUMDB=off "$audit_script" "$fixture_root"
)
after_cache=$(find "$cache_root" -mindepth 1 -print | LC_ALL=C sort)

assert_contains "$workspace_output" "workspace: $workspace_root/go.work"
assert_contains "$workspace_output" "dependency: github.com/goliatone/go-admin/quickstart"
assert_contains "$workspace_output" "  source-state: workspace-local"
assert_contains "$workspace_output" "  source-path: $module_root/go-admin-quickstart"
assert_contains "$workspace_output" "  source-go-version: 1.22"
assert_contains "$workspace_output" "  workspace-replacement: ./modules/go dashboard"
assert_contains "$workspace_output" "  source-state: workspace-replaced-local"
assert_contains "$workspace_output" "  source-path: $module_root/go dashboard"
[ "$before_cache" = "$after_cache" ] || fail "audit mutated the isolated module cache"

repeat_output=$(
  GOWORK="$workspace_root/go.work" GOMODCACHE="$cache_root" GOPROXY=off \
    GOSUMDB=off "$audit_script" "$fixture_root"
)
[ "$workspace_output" = "$repeat_output" ] || fail "audit output is not stable"

precedence_root=$test_root/precedence/go-admin
mkdir -p "$precedence_root/quickstart" "$precedence_root/alternate quickstart"
cat >"$precedence_root/go.mod" <<'EOF'
module github.com/goliatone/go-admin

go 1.22

require github.com/goliatone/go-admin/quickstart v9.9.9

replace github.com/goliatone/go-admin/quickstart => "./alternate quickstart"
EOF
cat >"$precedence_root/quickstart/go.mod" <<'EOF'
module github.com/goliatone/go-admin/quickstart

go 1.22
EOF
cat >"$precedence_root/alternate quickstart/go.mod" <<'EOF'
module github.com/goliatone/go-admin/quickstart

go 1.22
EOF

precedence_output=$(
  GOWORK=off GOMODCACHE="$cache_root" GOPROXY=off GOSUMDB=off \
    "$audit_script" "$precedence_root"
)
assert_contains "$precedence_output" "  replacement: ./alternate quickstart"
assert_contains "$precedence_output" "  source-state: replaced-local"
assert_contains "$precedence_output" \
  "  source-path: $precedence_root/alternate quickstart"

set +e
invalid_workspace_output=$(
  GOWORK="$test_root/missing.go.work" "$audit_script" "$fixture_root" 2>&1
)
invalid_workspace_exit=$?
set -e
[ "$invalid_workspace_exit" -eq 66 ] ||
  fail "invalid GOWORK returned $invalid_workspace_exit instead of 66"
assert_contains "$invalid_workspace_output" "active GOWORK file not found"

printf 'audit_go_admin_theme tests passed\n'
