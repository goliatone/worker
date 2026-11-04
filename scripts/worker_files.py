"""Small, shared file installer. Never follows destination symlinks."""
import hashlib
import argparse
import os
from pathlib import Path
import shutil
import tempfile
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def destination(home, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError(f'Invalid destination: {relative}')
    home = Path(home).resolve()
    target = home / relative
    for parent in target.parents:
        if parent == home:
            break
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError(f'Destination parent must be a real directory: {parent}')
    return target


def status(target, data, mode=0o600):
    if target.is_symlink():
        return 'different'
    if target.exists():
        if not target.is_file():
            raise ValueError(f'Expected a file: {target}')
        if target.read_bytes() == data and bool(target.stat().st_mode & 0o100) == bool(mode & 0o100):
            return 'same'
        return 'different'
    return 'missing'


def install_many(home, entries, *, dry_run=False, preserve_group=False):
    """Preflight, back up and stage a group before replacing any destination.

    Entries are (relative path, bytes, mode, replace). Caught write failures
    restore committed files; persistent backups remain available for recovery.
    This is not a filesystem transaction across a crash or concurrent writers.
    """
    pending = []
    seen = set()
    preserved = False
    for relative, data, mode, replace in entries:
        target = destination(home, relative)
        if target in seen:
            raise ValueError(f'Duplicate destination: {target}')
        seen.add(target)
        state = status(target, data, mode)
        if state == 'same':
            print(f'  Unchanged: {target}')
        elif state == 'different' and not replace:
            print(f'Notice: Preserved {target}; use --replace-config to back up and replace it.')
            preserved = True
        else:
            pending.append((target, data, mode, state))
    if preserved and preserve_group:
        print('Notice: No files in this group were changed.')
        return False
    backup_root = None
    if any(state == 'different' for _, _, _, state in pending):
        backup_root = destination(home, '.local/state/worker/backups/placeholder').parent
    if dry_run:
        for target, _, _, state in pending:
            print(f'  Would install: {target}')
            if state == 'different':
                print(f'  Would back up {target} before replacement.')
        return not preserved

    backups = {}
    staged = {}
    committed = []
    try:
        for target, data, mode, state in pending:
            if state == 'different':
                backup_root.mkdir(parents=True, exist_ok=True)
                backup = Path(tempfile.mkdtemp(prefix='config.', dir=backup_root))
                original = backup / target.name
                # Do not overwrite a saved file with our destination metadata.
                if target.name == 'destination.txt':
                    original = backup / 'original' / target.name
                    original.parent.mkdir()
                shutil.copy2(target, original, follow_symlinks=False)
                (backup / 'destination.txt').write_text(str(target) + '\n')
                backups[target] = original
                print(f'  Backup: {backup}')
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='.worker.', dir=target.parent)
            staged[target] = Path(temporary)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.chmod(temporary, mode)
        for target, _, _, _ in pending:
            print(f'  Install: {target}')
            os.replace(staged[target], target)
            committed.append(target)
    except BaseException as error:
        failed = []
        for target in reversed(committed):
            try:
                if target in backups:
                    temporary = staged[target]
                    shutil.copy2(backups[target], temporary, follow_symlinks=False)
                    os.replace(temporary, target)
                else:
                    target.unlink()
            except OSError:
                failed.append(str(target))
        if failed:
            raise OSError('Rollback failed for ' + ', '.join(failed) +
                          '; restore these files from ' + str(backup_root)) from error
        raise
    finally:
        for temporary in staged.values():
            if temporary.exists() or temporary.is_symlink():
                temporary.unlink()
    return not preserved


def install(home, relative, data, *, mode=0o600, replace=False, dry_run=False):
    return install_many(home, [(relative, data, mode, replace)], dry_run=dry_run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--replace-config', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        install(args.home, args.destination, Path(args.source).read_bytes(),
                replace=args.replace_config, dry_run=args.dry_run)
    except (ValueError, OSError) as error:
        print(f'Error: Configuration: {error}', file=sys.stderr)
        sys.exit(1)
