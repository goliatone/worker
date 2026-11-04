#!/usr/bin/env bash
[[ ${WORKER_LOADED:-0} == 1 ]] || { echo 'Run ./make, not individual modules.' >&2; exit 1; }

# Indexed arrays and an explicit count also work with Bash 3.2 and nounset.
CUSTOM_TAP_NAMES=()
CUSTOM_TAP_URLS=()
CUSTOM_TAP_COUNT=0

custom_tap_url() {
  local value=$1 allow_ssh=${2:-0} owner repository
  # Reject multiple lines before case folding can strip trailing newlines.
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || return 1
  value=$(printf '%s' "$value" | LC_ALL=C tr '[:upper:]' '[:lower:]') || return
  # Existing SSH origins can identify the same repository; new taps use HTTPS.
  if [[ $allow_ssh == 1 ]]; then
    case "$value" in
      https://github.com/*) ;;
      git@github.com:*)
        [[ "$1" == git@* ]] || return 1
        value="https://github.com/${value#git@github.com:}" ;;
      ssh://git@github.com/*)
        [[ "$1" =~ ^[sS][sS][hH]://git@ ]] || return 1
        value="https://github.com/${value#ssh://git@github.com/}" ;;
      # A scheme-less URL in Git config is a relative filesystem path, unlike
      # the convenient GitHub shorthand accepted in the user's input list.
      *) return 1 ;;
    esac
  fi
  value=${value#https://}
  value=${value%/}
  [[ "$value" =~ ^github\.com/([a-z0-9][a-z0-9-]*)/([a-z0-9][a-z0-9._-]*)$ ]] || return 1
  owner=${BASH_REMATCH[1]}
  repository=${BASH_REMATCH[2]%.git}
  [[ -n "$repository" && "$owner" != *- ]] || return 1
  printf 'https://github.com/%s/%s\n' "$owner" "$repository"
}

custom_tap_origin_url() {
  local repository=$1 output
  # Preserve all Git output until validation, including empty URL entries and
  # newlines inside values. Command substitution alone discards trailing LFs.
  output=$(
    env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR -u GIT_CONFIG \
      -u GIT_CONFIG_COUNT -u GIT_CONFIG_PARAMETERS git -C "$repository" \
      config --local --includes --get-all remote.origin.url && printf '.'
  ) || return 1
  [[ "$output" == *$'\n.' ]] || return 1
  output=${output%$'\n.'}
  custom_tap_url "$output" 1
}

load_custom_taps() {
  [[ -n "$TAPS_FILE" ]] || return 0
  [[ -f "$TAPS_FILE" && -r "$TAPS_FILE" ]] || die "Missing or unreadable taps file: $TAPS_FILE"
  # Absolute paths keep option-like filenames safe and resolve relative to the
  # caller, just like other file arguments. Freeze parsed entries in the arrays.
  case "$TAPS_FILE" in /*) ;; *) TAPS_FILE="$PWD/$TAPS_FILE" ;; esac
  # shellcheck disable=SC2094 # Both tr and cmp only read this file.
  if ! LC_ALL=C tr -d '\000' < "$TAPS_FILE" | cmp -s "$TAPS_FILE" -; then
    die "Taps file contains NUL bytes or could not be read: $TAPS_FILE"
  fi
  local line url name repository i duplicate line_number=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line_number=$((line_number + 1))
    line=${line%$'\r'}
    line=${line#"${line%%[!$' \t']*}"}
    line=${line%"${line##*[!$' \t']}"}
    [[ -n "$line" && "$line" != \#* ]] || continue
    if ! url=$(custom_tap_url "$line"); then
      die "Invalid GitHub repository at $TAPS_FILE:$line_number; use [https://]github.com/OWNER/REPOSITORY."
    fi
    name=${url#https://github.com/}
    repository=${name#*/}
    # Match Homebrew's canonical tap naming, preserving the exact repository URL.
    case "$repository" in homebrew-*|linuxbrew-*) repository=${repository#*-} ;; esac
    [[ "$repository" =~ ^[a-z0-9][a-z0-9._-]*$ ]] || die "Invalid tap name at $TAPS_FILE:$line_number."
    case "$repository" in
      homebrew-*|linuxbrew-*) die "Repeated Homebrew prefixes are ambiguous at $TAPS_FILE:$line_number." ;;
    esac
    name="${name%%/*}/$repository"
    # These historical aliases are remapped by Homebrew itself.
    case "$name" in homebrew/homebrew|linuxbrew/core|linuxbrew/homebrew) name=homebrew/core ;; esac
    duplicate=0
    for ((i=0; i<CUSTOM_TAP_COUNT; i++)); do
      if [[ "${CUSTOM_TAP_NAMES[i]}" == "$name" ]]; then
        [[ "${CUSTOM_TAP_URLS[i]}" == "$url" ]] || die "Conflicting repository URLs for tap $name in $TAPS_FILE."
        duplicate=1
        break
      fi
    done
    if [[ $duplicate == 0 ]]; then
      CUSTOM_TAP_NAMES[CUSTOM_TAP_COUNT]=$name
      CUSTOM_TAP_URLS[CUSTOM_TAP_COUNT]=$url
      CUSTOM_TAP_COUNT=$((CUSTOM_TAP_COUNT + 1))
    fi
  done < "$TAPS_FILE"
}

setup_custom_taps() {
  [[ -n "$TAPS_FILE" ]] || return 0
  log "Custom Homebrew taps: $TAPS_FILE"
  local i installed name repository normalized
  local missing=()
  if [[ $DRY_RUN == 1 ]]; then
    for ((i=0; i<CUSTOM_TAP_COUNT; i++)); do
      log "  Would keep ${CUSTOM_TAP_NAMES[i]} if its origin matches ${CUSTOM_TAP_URLS[i]}; otherwise add it if absent."
      run "$BREW_BIN" tap "${CUSTOM_TAP_NAMES[i]}" "${CUSTOM_TAP_URLS[i]}"
    done
    log '  Existing tap origins and remote availability are not checked in dry-run.'
    return 0
  fi
  [[ $CUSTOM_TAP_COUNT -gt 0 ]] || { log '  No taps requested.'; return 0; }
  installed=$("$BREW_BIN" tap) || die 'Could not list installed Homebrew taps; no custom taps were added.'
  # Check every requested origin before adding anything. Do not use remote
  # get-url: it applies Git URL rewrites rather than returning the stored URL.
  for ((i=0; i<CUSTOM_TAP_COUNT; i++)); do
    name=${CUSTOM_TAP_NAMES[i]}
    missing[i]=1
    if [[ $'\n'"$installed"$'\n' == *$'\n'"$name"$'\n'* ]]; then
      repository=$("$BREW_BIN" --repository "$name") || die "Could not locate installed tap $name."
      [[ "$repository" == /* && -d "$repository" ]] || die "Invalid checkout path for installed tap $name."
      # Homebrew lists tap directories even if a clone is incomplete. Do not
      # let Git discover the parent Homebrew repository and read its origin.
      [[ -d "$repository/.git" || -f "$repository/.git" ]] ||
        die "Installed tap $name has no Git metadata; review the incomplete checkout manually."
      normalized=$(custom_tap_origin_url "$repository") ||
        die "Could not read a single supported GitHub origin for tap $name (including local Git includes); review it manually."
      [[ "$normalized" == "${CUSTOM_TAP_URLS[i]}" ]] ||
        die "Installed tap $name points to a different repository; expected ${CUSTOM_TAP_URLS[i]}. Review it manually."
      missing[i]=0
      log "  Keep existing tap: $name"
    fi
  done
  for ((i=0; i<CUSTOM_TAP_COUNT; i++)); do
    [[ ${missing[i]} == 1 ]] || continue
    run "$BREW_BIN" tap "${CUSTOM_TAP_NAMES[i]}" "${CUSTOM_TAP_URLS[i]}" </dev/null
  done
}
