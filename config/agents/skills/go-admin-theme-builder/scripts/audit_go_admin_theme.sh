#!/bin/sh

# Read-only discovery index for go-admin theme work.
# Exit codes: 0 success (missing cached dependencies are diagnostic),
# 64 invalid usage, 66 invalid repository root, 69 missing required tools.

set -eu

usage() {
  printf 'usage: %s <repository-root>\n' "${0##*/}" >&2
}

die() {
  code=$1
  shift
  printf 'error: %s\n' "$*" >&2
  exit "$code"
}

if [ "$#" -ne 1 ]; then
  usage
  exit 64
fi

for audit_tool in awk find grep sed sort; do
  command -v "$audit_tool" >/dev/null 2>&1 ||
    die 69 "required tool not found: $audit_tool"
done

invocation_root=$(CDPATH='' cd . 2>/dev/null && pwd -P)
input_root=$1
[ -d "$input_root" ] || die 66 "repository root is not a directory: $input_root"

repo_root=$(CDPATH='' cd "$input_root" 2>/dev/null && pwd -P) ||
  die 66 "cannot resolve repository root: $input_root"
go_mod=$repo_root/go.mod
[ -f "$go_mod" ] || die 66 "go.mod not found at repository root: $repo_root"

module_identity=$(
  awk '$1 == "module" { print $2; exit }' "$go_mod"
)
go_version=$(
  awk '$1 == "go" { print $2; exit }' "$go_mod"
)
[ -n "$module_identity" ] || die 66 "module directive not found: $go_mod"

module_identity_from() {
  identity_file=$1
  [ -f "$identity_file" ] || return
  awk '$1 == "module" { print $2; exit }' "$identity_file"
}

module_go_version_from() {
  version_file=$1
  [ -f "$version_file" ] || return
  awk '$1 == "go" { print $2; exit }' "$version_file"
}

module_version() {
  version_target=$1
  awk -v target="$version_target" '
    $1 == "require" && $2 == "(" { in_require = 1; next }
    in_require && $1 == ")" { in_require = 0; next }
    in_require && $1 == target { print $2; exit }
    $1 == "require" && $2 == target { print $3; exit }
  ' "$go_mod"
}

replacement_from() {
  replacement_file=$1
  replacement_target=$2
  [ -f "$replacement_file" ] || return
  awk -v target="$replacement_target" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }
    function emit(line, rhs, quoted, closing, tail, fields, count) {
      sub(/^.*=>[[:space:]]*/, "", line)
      rhs = trim(line)
      if (substr(rhs, 1, 1) == "\"") {
        quoted = substr(rhs, 2)
        closing = index(quoted, "\"")
        if (closing == 0) return
        replacement_path = substr(quoted, 1, closing - 1)
        tail = trim(substr(quoted, closing + 1))
        count = split(tail, fields, /[[:space:]]+/)
        replacement_version = count > 0 ? fields[1] : ""
      } else {
        count = split(rhs, fields, /[[:space:]]+/)
        replacement_path = fields[1]
        replacement_version = count > 1 ? fields[2] : ""
      }
      print replacement_path "|" replacement_version
    }
    $1 == "replace" && $2 == "(" { in_replace = 1; next }
    in_replace && $1 == ")" { in_replace = 0; next }
    in_replace && $1 == target {
      emit($0)
      exit
    }
    $1 == "replace" && $2 == target {
      emit($0)
      exit
    }
  ' "$replacement_file"
}

module_cache_root() {
  if [ -n "${GOMODCACHE:-}" ]; then
    printf '%s\n' "$GOMODCACHE"
    return
  fi
  if command -v go >/dev/null 2>&1; then
    GOWORK=off GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly \
      go env GOMODCACHE 2>/dev/null || true
  fi
}

resolve_path_from() {
  path_base=$1
  path_candidate=$2
  case "$path_candidate" in
    /*) resolved_path=$path_candidate ;;
    *) resolved_path=$path_base/$path_candidate ;;
  esac
  if [ -d "$resolved_path" ]; then
    (CDPATH='' cd "$resolved_path" 2>/dev/null && pwd -P)
  else
    printf '%s\n' "$resolved_path"
  fi
}

resolve_file_from() {
  file_base=$1
  file_candidate=$2
  case "$file_candidate" in
    /*) unresolved_file=$file_candidate ;;
    *) unresolved_file=$file_base/$file_candidate ;;
  esac
  [ -f "$unresolved_file" ] || return
  unresolved_dir=${unresolved_file%/*}
  unresolved_name=${unresolved_file##*/}
  resolved_dir=$(CDPATH='' cd "$unresolved_dir" 2>/dev/null && pwd -P) || return
  printf '%s/%s\n' "$resolved_dir" "$unresolved_name"
}

detect_go_work() {
  detected_work=
  if [ "${GOWORK+x}" = x ]; then
    case "$GOWORK" in
      off) return 0 ;;
      ""|auto)
        if command -v go >/dev/null 2>&1; then
          detected_work=$(
            CDPATH='' cd "$repo_root" 2>/dev/null &&
              GOWORK=auto GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly \
                go env GOWORK 2>/dev/null ||
              true
          )
        fi
        ;;
      *)
        detected_work=$(resolve_file_from "$invocation_root" "$GOWORK" || true)
        [ -n "$detected_work" ] ||
          die 66 "active GOWORK file not found: $GOWORK"
        ;;
    esac
  elif command -v go >/dev/null 2>&1; then
    detected_work=$(
      CDPATH='' cd "$repo_root" 2>/dev/null &&
        GOWORK=auto GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly \
          go env GOWORK 2>/dev/null ||
        true
    )
    case "$detected_work" in
      ""|off) return 0 ;;
    esac
    detected_work=$(resolve_file_from "$repo_root" "$detected_work" || true)
    [ -n "$detected_work" ] ||
      die 66 "auto-selected GOWORK file not found"
  fi
  [ -n "$detected_work" ] && printf '%s\n' "$detected_work"
}

active_go_work=$(detect_go_work)
go_work_root=
[ -z "$active_go_work" ] || go_work_root=${active_go_work%/*}

workspace_use_paths() {
  [ -n "$active_go_work" ] && [ -f "$active_go_work" ] || return
  awk '
    function clean(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      if (value ~ /^".*"$/) {
        value = substr(value, 2, length(value) - 2)
      }
      return value
    }
    $1 == "use" && $2 == "(" { in_use = 1; next }
    in_use && $1 == ")" { in_use = 0; next }
    in_use {
      value = clean($0)
      if (value != "" && value !~ /^\/\//) print value
      next
    }
    $1 == "use" {
      value = $0
      sub(/^[[:space:]]*use[[:space:]]+/, "", value)
      value = clean(value)
      if (value != "") print value
    }
  ' "$active_go_work"
}

workspace_source_for() {
  workspace_target=$1
  workspace_use_paths |
    while IFS= read -r workspace_entry; do
      workspace_path=$(resolve_path_from "$go_work_root" "$workspace_entry")
      workspace_identity=$(module_identity_from "$workspace_path/go.mod" || true)
      if [ "$workspace_identity" = "$workspace_target" ]; then
        printf '%s\n' "$workspace_path"
        break
      fi
    done
}

nested_source_for() {
  nested_target=$1
  nested_path=$repo_root/quickstart
  nested_identity=$(module_identity_from "$nested_path/go.mod" || true)
  if [ "$nested_identity" = "$nested_target" ]; then
    printf '%s\n' "$nested_path"
  fi
}

resolve_replacement() {
  resolved_replacement=$1
  replacement_base=$2
  replacement_state_prefix=$3
  replacement_fallback_version=$4

  resolved_target=${resolved_replacement%%|*}
  resolved_version=${resolved_replacement#*|}
  RESOLVED_REPLACEMENT_TEXT=$resolved_target
  [ -n "$resolved_version" ] &&
    RESOLVED_REPLACEMENT_TEXT="$resolved_target $resolved_version"
  case "$resolved_target" in
    .|..|./*|../*|/*)
      RESOLVED_REPLACEMENT_PATH=$(resolve_path_from "$replacement_base" "$resolved_target")
      if [ -d "$RESOLVED_REPLACEMENT_PATH" ]; then
        RESOLVED_REPLACEMENT_STATE=$replacement_state_prefix-local
      else
        RESOLVED_REPLACEMENT_STATE=missing-$replacement_state_prefix
      fi
      ;;
    *)
      replacement_cache=$(module_cache_root)
      replacement_cache_version=$resolved_version
      [ -n "$replacement_cache_version" ] ||
        replacement_cache_version=$replacement_fallback_version
      RESOLVED_REPLACEMENT_PATH=
      RESOLVED_REPLACEMENT_STATE=missing-$replacement_state_prefix-cache
      if [ -n "$replacement_cache" ] && [ -n "$replacement_cache_version" ]; then
        RESOLVED_REPLACEMENT_PATH=$replacement_cache/$resolved_target@$replacement_cache_version
        if [ -d "$RESOLVED_REPLACEMENT_PATH" ]; then
          RESOLVED_REPLACEMENT_STATE=$replacement_state_prefix-cache
        fi
      fi
      ;;
  esac
}

dependency_record() {
  dependency=$1
  version=$(module_version "$dependency")
  module_replacement=$(replacement_from "$go_mod" "$dependency")
  workspace_replacement=
  [ -z "$active_go_work" ] ||
    workspace_replacement=$(replacement_from "$active_go_work" "$dependency")
  workspace_source=$(workspace_source_for "$dependency" || true)
  nested_source=$(nested_source_for "$dependency" || true)
  source_state=missing
  source_path=
  replacement_text=none
  workspace_replacement_text=none

  if [ "$dependency" = "$module_identity" ]; then
    source_state=local
    source_path=$repo_root
  elif [ -n "$workspace_source" ]; then
    source_state=workspace-local
    source_path=$workspace_source
  elif [ -n "$workspace_replacement" ]; then
    resolve_replacement "$workspace_replacement" "$go_work_root" \
      workspace-replaced "$version"
    source_state=$RESOLVED_REPLACEMENT_STATE
    source_path=$RESOLVED_REPLACEMENT_PATH
    workspace_replacement_text=$RESOLVED_REPLACEMENT_TEXT
  elif [ -n "$module_replacement" ]; then
    resolve_replacement "$module_replacement" "$repo_root" replaced "$version"
    source_state=$RESOLVED_REPLACEMENT_STATE
    source_path=$RESOLVED_REPLACEMENT_PATH
    replacement_text=$RESOLVED_REPLACEMENT_TEXT
  elif [ -n "$nested_source" ]; then
    source_state=local-nested
    source_path=$nested_source
  elif [ -n "$version" ]; then
    dependency_cache=$(module_cache_root)
    if [ -n "$dependency_cache" ]; then
      source_path=$dependency_cache/$dependency@$version
      if [ -d "$source_path" ]; then
        source_state=module-cache
      else
        source_state=missing-cache
      fi
    fi
  else
    source_state=not-required
  fi

  resolved_module=
  resolved_go_version=
  if [ -n "$source_path" ]; then
    resolved_module=$(module_identity_from "$source_path/go.mod" || true)
    resolved_go_version=$(module_go_version_from "$source_path/go.mod" || true)
  fi
  printf 'dependency: %s\n' "$dependency"
  printf '  requirement: %s\n' "${version:-none}"
  printf '  replacement: %s\n' "$replacement_text"
  printf '  workspace-replacement: %s\n' "$workspace_replacement_text"
  printf '  source-state: %s\n' "$source_state"
  printf '  source-path: %s\n' "${source_path:-unresolved}"
  printf '  source-module: %s\n' "${resolved_module:-unknown}"
  printf '  source-go-version: %s\n' "${resolved_go_version:-unknown}"
  AUDIT_LAST_PATH=$source_path
}

rank_matches() {
  match_root=$1
  match_priority=$2
  match_limit=$3
  awk -v root="$match_root/" -v priority="$match_priority" -v limit="$match_limit" '
    {
      files[++count] = $0
      preferred[count] = ($0 ~ priority)
    }
    END {
      emitted = 0
      for (i = 1; i <= count; i++) {
        if (preferred[i]) {
          path = files[i]
          if (index(path, root) == 1) path = substr(path, length(root) + 1)
          printf "    %s\n", path
          emitted++
        }
      }
      for (i = 1; i <= count && emitted < limit; i++) {
        if (!preferred[i]) {
          path = files[i]
          if (index(path, root) == 1) path = substr(path, length(root) + 1)
          printf "    %s\n", path
          emitted++
        }
      }
      if (count > emitted) {
        printf "    ... %d additional matches omitted\n", count - emitted
      }
    }
  '
}

matching_files() {
  source_label=$1
  source_root=$2
  pattern=$3
  priority_pattern=$4
  printf '  source: %s\n' "$source_label"
  if [ ! -d "$source_root" ]; then
    printf '    unavailable\n'
    return
  fi

  if command -v rg >/dev/null 2>&1; then
    {
      if [ "$source_label" = go-admin ]; then
        rg -l --no-messages \
          -g '*.go' -g '*.html' -g '*.css' -g '*.js' -g '*.ts' -g '*.cjs' \
          -g 'package.json' -g '!quickstart/**' -g '!**/node_modules/**' \
          -g '!**/vendor/**' -g '!**/dist/**' -g '!**/.git/**' \
          -g '!**/.ctx/**' -g '!**/testdata/**' \
          "$pattern" "$source_root"
      else
        rg -l --no-messages \
          -g '*.go' -g '*.html' -g '*.css' -g '*.js' -g '*.ts' -g '*.cjs' \
          -g 'package.json' -g '!**/node_modules/**' -g '!**/vendor/**' \
          -g '!**/dist/**' -g '!**/.git/**' -g '!**/.ctx/**' \
          -g '!**/testdata/**' \
          "$pattern" "$source_root"
      fi
    } |
      LC_ALL=C sort |
      rank_matches "$source_root" "$priority_pattern" 40
    return
  fi

  {
    if [ "$source_label" = go-admin ]; then
      find "$source_root" \
        \( -type d \( -name .git -o -name .ctx -o -name quickstart -o \
           -name node_modules -o -name vendor -o -name dist -o \
           -name testdata \) -prune \) -o \
        \( -type f \( -name '*.go' -o -name '*.html' -o -name '*.css' -o \
           -name '*.js' -o -name '*.ts' -o -name '*.cjs' -o \
           -name 'package.json' \) -exec grep -El "$pattern" {} \; \) 2>/dev/null
    else
      find "$source_root" \
        \( -type d \( -name .git -o -name .ctx -o -name node_modules -o \
           -name vendor -o -name dist -o -name testdata \) -prune \) -o \
        \( -type f \( -name '*.go' -o -name '*.html' -o -name '*.css' -o \
           -name '*.js' -o -name '*.ts' -o -name '*.cjs' -o \
           -name 'package.json' \) -exec grep -El "$pattern" {} \; \) 2>/dev/null
    fi
  } |
    LC_ALL=C sort |
    rank_matches "$source_root" "$priority_pattern" 40
}

printf 'go-admin theme audit\n'
printf 'repository-root: %s\n' "$repo_root"
printf 'module: %s\n' "$module_identity"
printf 'go-version: %s\n' "${go_version:-unknown}"
printf 'workspace: %s\n' "${active_go_work:-none}"
printf 'network-policy: disabled\n'
printf 'mutation-policy: read-only\n'

go_admin_source=
go_quickstart_source=
go_theme_source=
go_formgen_source=
go_dashboard_source=

for dependency in \
  github.com/goliatone/go-admin \
  github.com/goliatone/go-admin/quickstart \
  github.com/goliatone/go-theme \
  github.com/goliatone/go-formgen \
  github.com/goliatone/go-dashboard
do
  dependency_record "$dependency"
  case "$dependency" in
    github.com/goliatone/go-admin) go_admin_source=$AUDIT_LAST_PATH ;;
    github.com/goliatone/go-admin/quickstart) go_quickstart_source=$AUDIT_LAST_PATH ;;
    github.com/goliatone/go-theme) go_theme_source=$AUDIT_LAST_PATH ;;
    github.com/goliatone/go-formgen) go_formgen_source=$AUDIT_LAST_PATH ;;
    github.com/goliatone/go-dashboard) go_dashboard_source=$AUDIT_LAST_PATH ;;
  esac
done

printf 'contract-area: selector-and-provider-wiring\n'
matching_files go-admin "$go_admin_source" \
  'ThemeSelector|ThemeProvider|NewThemeSelector|WithAdminTheme|WithThemeContext' \
  '/admin/theme(_adapter|_test)?\.go$'
matching_files go-admin/quickstart "$go_quickstart_source" \
  'ThemeSelector|ThemeProvider|NewThemeSelector|WithAdminTheme|WithThemeContext' \
  '(^|/)(theme_selector|admin_bootstrap|site/theme_provider).*\.go$'

printf 'contract-area: template-layering\n'
matching_files go-admin "$go_admin_source" \
  'TemplateFS|TemplateFileSystem|ViewFS|view filesystem|first.wins|templates' \
  '(^|/)(admin/.*template|pkg/client/templates/)'
matching_files go-admin/quickstart "$go_quickstart_source" \
  'TemplateFS|TemplateFileSystem|ViewFS|view filesystem|first.wins|templates' \
  '(^|/)(view_engine|template_fs).*\.go$'

printf 'contract-area: asset-layering-and-static-delivery\n'
matching_files go-admin "$go_admin_source" \
  'AssetFS|StaticFS|StaticAssets|WithThemeAssets|AssetPrefix|embedded assets' \
  '(^|/)(admin/theme|pkg/client/assets)'
matching_files go-admin/quickstart "$go_quickstart_source" \
  'AssetFS|StaticFS|StaticAssets|WithThemeAssets|AssetPrefix|embedded assets' \
  '(^|/)static_assets.*\.go$'

printf 'contract-area: client-build-entries\n'
matching_files go-admin "$go_admin_source" \
  'tailwind|postcss|npm run build|input\.css|datatable|packageManager' \
  '(^|/)pkg/client/assets/(package\.json|input\.css|.*config\.(js|ts|cjs))$'

printf 'contract-area: go-admin-token-consumers\n'
matching_files go-admin "$go_admin_source" \
  'theme\.tokens|ThemeTokens|CSSVariables|css_vars|--admin-|--theme-' \
  '(^|/)admin/(theme|theme_adapter|layout_view_context).*\.go$'
matching_files go-admin/quickstart "$go_quickstart_source" \
  'theme\.tokens|ThemeTokens|CSSVariables|css_vars|--admin-|--theme-' \
  '(^|/)(admin_config|theme_selector|site/theme_).*\.go$'

printf 'contract-area: go-theme-manifest-and-variants\n'
matching_files go-theme "$go_theme_source" \
  'type Manifest|type Variant|Tokens|CSSVariables|Selector|Resolve' \
  '(^|/)(manifest|selector|registry).*\.go$'

printf 'contract-area: go-formgen-theme-seams\n'
matching_files go-formgen "$go_formgen_source" \
  'ThemeConfig|CSSVariables|ThemeAssets|ThemeSelector|theme' \
  '(^|/)(pkg/render/options|pkg/orchestrator/defaults/defaults).*\.go$'

printf 'contract-area: go-dashboard-theme-seams\n'
matching_files go-dashboard "$go_dashboard_source" \
  'ThemeSelection|ThemeProvider|ThemeSelector|CSSVariables|ChartTheme' \
  '(^|/)components/dashboard/(theme|provider|page).*\.go$'

printf 'contract-area: focused-tests\n'
matching_files go-admin "$go_admin_source" \
  'Test[A-Za-z0-9_]*(Theme|ThemeSelector|View|Static|SiteTheme)' \
  '(^|/)admin/theme_test\.go$'
matching_files go-admin/quickstart "$go_quickstart_source" \
  'Test[A-Za-z0-9_]*(Theme|ThemeSelector|View|Static|SiteTheme)' \
  '(^|/)(theme_selector|view_engine|static_assets).*_test\.go$'

printf 'manual-fallback: read go.mod, active go.work use/replace directives, and module replacements; inspect resolved local or cached go-admin and quickstart sources; locate selector/provider, manifest, template and asset filesystem composition, client build entries, token consumers, and focused tests without downloading modules\n'
