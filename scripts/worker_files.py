"""Small, shared file installer. Never follows destination symlinks."""
import hashlib
import os
from pathlib import Path
import shutil
import tempfile


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


def install(home, relative, data, *, mode=0o600, replace=False, dry_run=False):
    target = destination(home, relative)
    state = status(target, data, mode)
    if state == 'same':
        print(f'  Unchanged: {target}')
        return True
    if state == 'different' and not replace:
        print(f'Notice: Preserved {target}; use --replace-config to back up and replace it.')
        return False
    print(f'  {"Would install" if dry_run else "Install"}: {target}')
    if dry_run:
        if state == 'different':
            print(f'  Would back up {target} before replacement.')
        return True
    if state == 'different':
        backup_root = destination(home, '.local/state/worker/backups/placeholder').parent
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix='config.', dir=backup_root))
        shutil.copy2(target, backup / target.name, follow_symlinks=False)
        (backup / 'destination.txt').write_text(str(target) + '\n')
        print(f'  Backup: {backup}')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.worker.', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True
