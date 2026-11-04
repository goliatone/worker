"""Build pinned upstream tools and helpers in temporary storage."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

from worker_files import destination, install
from go_metadata import validate_binary
from custom_workflow import build_environment, setup_custom


def setup(root, home, arch, replace=False):
    root = Path(root)
    helpers = []
    for line in (root / 'extensions/go-workflow-tools.txt').read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        fields = line.split()
        if len(fields) != 2 or not re.fullmatch(r'[a-zA-Z0-9_-]+', fields[0]) or not re.fullmatch(r'[a-zA-Z0-9./_-]+@v[0-9][a-zA-Z0-9.+-]*', fields[1]):
            raise ValueError(f'Invalid workflow Go manifest entry: {line}')
        helpers.append(fields)
    for name in ('ai-shot', 'ctx.sh'):
        install(home, 'bin/' + name, (root / 'config/workflow' / name).read_bytes(), mode=0o700, replace=replace)
    deferred = setup_custom(root, home, arch, replace)
    for binary, spec in helpers:
        package, version = spec.rsplit('@', 1)
        target = destination(home, 'go/bin/' + binary)
        if target.is_file() and not target.is_symlink() and os.access(target, os.X_OK):
            try:
                validate_binary(target, package, arch, version)
                print(f'  Already installed: {binary}@{version}')
                continue
            except (ValueError, subprocess.CalledProcessError):
                pass
        if (target.exists() or target.is_symlink()) and not replace:
            deferred = True
            print(f'Notice: Preserved {target}; use --replace-config to back up and replace this helper.')
            continue
        with tempfile.TemporaryDirectory(prefix='worker-go-') as temporary:
            print(f'  Build {spec} for darwin/{arch}', flush=True)
            env = {**build_environment(arch, private=False), 'GOBIN': temporary}
            subprocess.run(['go', 'install', spec], env=env, cwd=temporary, stdin=subprocess.DEVNULL, check=True)
            built = Path(temporary) / binary
            validate_binary(built, package, arch, version)
            install(home, 'go/bin/' + binary, built.read_bytes(), mode=0o700, replace=replace)

    return 2 if deferred else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--home', required=True)
    parser.add_argument('--arch', required=True, choices=('arm64', 'amd64'))
    parser.add_argument('--replace-config', action='store_true')
    args = parser.parse_args()
    try:
        sys.exit(setup(args.root, args.home, args.arch, args.replace_config))
    except (ValueError, OSError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f'Error: Workflow tools: {error}', file=sys.stderr)
        sys.exit(1)
