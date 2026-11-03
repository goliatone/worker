"""Build explicit GitHub revisions without changing the user's source checkouts."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile

from go_metadata import validate_binary
from worker_files import destination, digest, install, status


def extract(archive, target):
    # GitHub archives have one root directory. Reject links and traversal before
    # writing any member, even though the source is an explicitly selected repo.
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        roots = set()
        size = 0
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or not (member.isfile() or member.isdir()):
                raise ValueError(f'Unsafe source archive member: {member.name}')
            roots.add(path.parts[0])
            size += member.size
        if len(roots) != 1 or size > 268435456:
            raise ValueError('Source archive must have one root and be smaller than 256 MiB.')
        for member in members:
            relative = PurePosixPath(member.name).parts[1:]
            if not relative:
                continue
            path = target.joinpath(*relative)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with stream.extractfile(member) as source, path.open('wb') as output:
                    shutil.copyfileobj(source, output)


def build_environment(arch, private):
    env = {**os.environ, 'GOOS': 'darwin', 'GOARCH': arch, 'GOWORK': 'off', 'GOFLAGS': '',
           'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0'}
    if private:
        env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='credential.https://github.com.helper',
                   GIT_CONFIG_VALUE_0='!gh auth git-credential')
        for name in ('GOPRIVATE', 'GONOPROXY', 'GONOSUMDB'):
            env[name] = ','.join(filter(None, [env.get(name), 'github.com/goliatone/*']))
    return env


def validate_manifest(entries):
    expected = {'ctx': 'go/bin/ctx', 'gengql': 'bin/gengql', 'g': 'bin/g'}
    if not isinstance(entries, list) or len(entries) != 3 or not all(isinstance(x, dict) for x in entries) or {x.get('name') for x in entries} != set(expected):
        raise ValueError('Custom tool manifest must define ctx, gengql, and g exactly once.')
    for entry in entries:
        if (entry.get('destination') != expected[entry['name']] or
                not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', entry.get('repo', '')) or
                not re.fullmatch(r'[0-9a-f]{40}', entry.get('revision', '')) or
                entry.get('package') not in ('.', './cmd/ctx', './cmd/gql-gen') or
                not isinstance(entry.get('private'), bool)):
            raise ValueError('Invalid custom tool manifest entry.')
        assets = entry.get('assets', {})
        if assets and (entry['name'] != 'ctx' or assets != {'internal/ctxassets/defaults/assets/zsh/_ctx': '.zsh/completions/_ctx'}):
            raise ValueError('Unsupported custom tool asset mapping.')


def setup_custom(root, home, arch, replace=False):
    entries = json.loads((Path(root) / 'extensions/custom-workflow-tools.json').read_text())
    validate_manifest(entries)
    deferred = False
    authenticated = None
    for entry in entries:
        name = entry['name']
        target = destination(home, entry['destination'])
        receipt_path = '.local/state/worker/tools/' + name + '.json'
        receipt_file = destination(home, receipt_path)
        receipt = {}
        if receipt_file.is_file() and not receipt_file.is_symlink():
            try:
                receipt = json.loads(receipt_file.read_text())
            except ValueError:
                pass
        if not isinstance(receipt, dict):
            receipt = {}
        wanted = {'repo': entry['repo'], 'revision': entry['revision'], 'arch': arch,
                  'package': entry['go_path']}
        if all(receipt.get(k) == v for k, v in wanted.items()) and target.is_file() and not target.is_symlink() and os.access(target, os.X_OK):
            matches = receipt.get('sha256') == digest(target.read_bytes())
            for relative in entry['assets'].values():
                asset = destination(home, relative)
                matches = matches and asset.is_file() and not asset.is_symlink() and receipt.get('assets', {}).get(relative) == digest(asset.read_bytes())
            if matches:
                print(f'  Keep verified upstream build: {name}@{entry["revision"][:12]}')
                continue
        if (target.exists() or target.is_symlink()) and not replace and not receipt:
            print(f'Notice: Preserved existing custom {target}; use --replace-config to back up and install the pinned upstream build.')
            deferred = True
            continue
        if entry['private']:
            if authenticated is None:
                authenticated = subprocess.run(['gh', 'auth', 'status', '--hostname', 'github.com'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
            if not authenticated:
                print(f'Notice: {name} deferred: run gh auth login with access to {entry["repo"]}, then rerun --with-workflow.')
                deferred = True
                continue
        with tempfile.TemporaryDirectory(prefix='worker-source-') as temporary:
            temporary = Path(temporary)
            archive = temporary / 'source.tar.gz'
            if entry['private']:
                with archive.open('wb') as output:
                    subprocess.run(['gh', 'api', f'repos/{entry["repo"]}/tarball/{entry["revision"]}'], stdout=output, check=True, stdin=subprocess.DEVNULL)
            else:
                subprocess.run(['curl', '--fail', '--silent', '--show-error', '--proto', '=https',
                                '--connect-timeout', '15', '--max-time', '120', '--max-filesize', '67108864',
                                '--url', f'https://codeload.github.com/{entry["repo"]}/tar.gz/{entry["revision"]}',
                                '-o', str(archive)], check=True, stdin=subprocess.DEVNULL)
            source = temporary / 'source'; source.mkdir()
            extract(archive, source)
            assets = {}
            for relative, installed in entry['assets'].items():
                file = source / relative
                subprocess.run(['/bin/zsh', '-dfn', str(file)], check=True, capture_output=True)
                assets[installed] = file.read_bytes()
            binary = temporary / name
            print(f'  Build clean upstream {entry["repo"]}@{entry["revision"][:12]}', flush=True)
            subprocess.run(['go', 'build', '-mod=readonly', '-trimpath', '-buildvcs=false', '-o', str(binary), entry['package']],
                           cwd=source, env=build_environment(arch, entry['private']), check=True, stdin=subprocess.DEVNULL)
            validate_binary(binary, entry['go_path'], arch)
            data = binary.read_bytes()
            outputs = [(entry['destination'], data, 0o700)] + [(p, d, 0o600) for p, d in assets.items()]
            if not replace and any(status(destination(home, p), d, mode) == 'different' for p, d, mode in outputs):
                print(f'Notice: Preserved differing {name} binary/completion; use --replace-config. No files for this tool were changed.')
                deferred = True
                continue
            for p, d, mode in outputs:
                install(home, p, d, mode=mode, replace=replace)
            wanted.update(sha256=digest(data), assets={p: digest(d) for p, d in assets.items()})
            install(home, receipt_path, (json.dumps(wanted, indent=2, sort_keys=True) + '\n').encode(), replace=True)
    return deferred
