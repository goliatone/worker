#!/usr/bin/env bash

log() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
notice() { WARNINGS=$((WARNINGS + 1)); printf 'Notice: %s\n' "$*" >&2; }

run() {
  printf '  +'; printf ' %q' "$@"; printf '\n'
  if [[ $DRY_RUN == 0 ]]; then "$@"; fi
}

# Migrate only the blanket rewrite shipped by older worker snapshots. Homebrew
# filters GIT_* overrides, so this must happen on disk before its first command.
repair_legacy_git_rewrite() {
  local config="$WORKER_HOME/.gitconfig" key='url.git@github.com:.insteadOf'
  local value='https://github.com/' status backup_dir
  [[ -f "$config" ]] || return 0
  # Apple's Git can open the CLT installer when the tools are missing. A dry run
  # must not invoke that stub; normal runs already checked CLT in setup_brew.
  if [[ $DRY_RUN == 1 ]] && ! xcode-select -p >/dev/null 2>&1; then
    log "  Would check $config for the legacy GitHub URL rewrite after Command Line Tools are installed."
    return 0
  fi
  if git config --file "$config" --no-includes --fixed-value --get-all "$key" "$value" >/dev/null; then
    :
  else
    status=$?
    [[ $status == 1 ]] && return 0
    die "Could not inspect Git configuration at $config; no repair was attempted."
  fi
  [[ ! -L "$config" && -O "$config" && -w "$config" ]] ||
    die "Legacy GitHub rewrite found in $config, but automatic repair requires a writable regular file owned by you (not a symlink)."
  if [[ $DRY_RUN == 1 ]]; then
    log "  Would back up $config under $WORKER_HOME/.local/state/worker/backups/git-url-rewrite.*/ and remove only $key = $value."
    return 0
  fi
  if ! mkdir -p "$WORKER_HOME/.local/state/worker/backups" ||
     ! backup_dir=$(mktemp -d "$WORKER_HOME/.local/state/worker/backups/git-url-rewrite.XXXXXX") ||
     ! cp -p "$config" "$backup_dir/.gitconfig" ||
     ! printf '%s\n' "$config" > "$backup_dir/destination.txt"; then
    die "Could not back up $config; no repair was attempted."
  fi
  log "  Git URL rewrite backup: $backup_dir"
  # Git locks and atomically updates this file, preserving other values. Do not
  # bypass an existing .lock or modify anything reached through an include.
  if ! git config --file "$config" --no-includes --fixed-value --unset-all "$key" "$value"; then
    die "Could not repair $config. Backup: $backup_dir/.gitconfig. Resolve the Git error and rerun."
  fi
  log "  Repaired legacy GitHub HTTPS-to-SSH rewrite in $config."
}

# Copies allow moving the checkout later. Never silently replace existing files.
install_file() {
  local src=$1 dst=$2 parent backup_dir temporary
  [[ -f "$src" ]] || die "Missing configuration source: $src"
  if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
    log "  Unchanged: $dst"
    return
  fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    [[ ! -d "$dst" || -L "$dst" ]] || die "Expected a file, found a directory: $dst"
    if [[ $REPLACE_CONFIG == 0 ]]; then
      notice "Preserved $dst; use --replace-config to back it up and install the snapshot."
      return
    fi
    if [[ $DRY_RUN == 1 ]]; then
      log "  Would back up $dst under $WORKER_HOME/.local/state/worker/backups/"
    else
      mkdir -p "$WORKER_HOME/.local/state/worker/backups"
      backup_dir=$(mktemp -d "$WORKER_HOME/.local/state/worker/backups/config.XXXXXX")
      cp -Pp "$dst" "$backup_dir/$(basename "$dst")"
      printf '%s\n' "$dst" > "$backup_dir/destination.txt"
      log "  Backup: $backup_dir"
    fi
  fi
  log "  Install config: $src -> $dst"
  [[ $DRY_RUN == 0 ]] || return 0
  parent=$(dirname "$dst")
  mkdir -p "$parent"
  temporary=$(mktemp "$parent/.worker.XXXXXX")
  cp "$src" "$temporary"
  chmod 600 "$temporary"
  # mv treats symlinks to directories as directories on some platforms.
  # Unlink only the backed-up link, never its target.
  if [[ -L "$dst" ]]; then rm "$dst"; fi
  mv -f "$temporary" "$dst"
}

clone_public_repo() {
  local url=$1 ref=$2 destination=$3 sentinel=$4 patch_file=${5:-} staging
  [[ -z "$patch_file" || -f "$patch_file" ]] || die "Missing dependency patch: $patch_file"
  if [[ -f "$destination/$sentinel" ]]; then
    log "  Keep existing checkout: $destination"
    return
  fi
  [[ ! -e "$destination" && ! -L "$destination" ]] || die "Incomplete checkout at $destination; move it aside and rerun."
  if [[ $DRY_RUN == 1 ]]; then
    log "  Would clone $url at $ref into $destination (public HTTPS, ignoring Git URL rewrites)."
    [[ -z "$patch_file" ]] || log "  Would apply captured local changes from $patch_file before installing the checkout."
    return
  fi
  mkdir -p "$(dirname "$destination")"
  staging=$(mktemp -d "$(dirname "$destination")/.worker-clone.XXXXXX")
  # Public bootstrap dependencies must not require SSH keys or global URL rewrites.
  if ! env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git clone "$url" "$staging" ||
     ! env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -C "$staging" checkout --detach "$ref" ||
     [[ ! -f "$staging/$sentinel" ]]; then
    rm -rf "$staging"
    die "Could not prepare $url at $ref; destination was not changed."
  fi
  if [[ -n "$patch_file" ]] && ! env GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 git -C "$staging" apply "$patch_file"; then
    rm -rf "$staging"
    die "Could not apply $patch_file; destination was not changed."
  fi
  mv "$staging" "$destination"
}
