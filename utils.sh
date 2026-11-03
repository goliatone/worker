#!/usr/bin/env bash

log() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
notice() { WARNINGS=$((WARNINGS + 1)); printf 'Notice: %s\n' "$*" >&2; }

run() {
  printf '  +'; printf ' %q' "$@"; printf '\n'
  if [[ $DRY_RUN == 0 ]]; then "$@"; fi
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
