"""Install an explicitly selected, immutable gist; never execute its contents."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from worker_files import destination, digest, install_many

FILES = ('zshrc.shared', 'gitconfig.shared', 'zshrc.shared.pre')
EARLY = '[[ ! -r "$HOME/.config/worker/zshrc.shared.pre" ]] || source "$HOME/.config/worker/zshrc.shared.pre"\n'
LATE = '[[ ! -r "$HOME/.config/worker/zshrc.shared" ]] || source "$HOME/.config/worker/zshrc.shared"\n'
LOCAL = '[[ ! -r "$HOME/.zshrc.local" ]] || source "$HOME/.zshrc.local"\n'
GIT_SHARED = '[include]\n  path = ~/.config/worker/gitconfig.shared\n'
GIT_LOCAL = '[include]\n  path = ~/.gitconfig.local\n'


def parse_source(url, revision):
    match = re.fullmatch(r'https://gist\.github\.com/(?:[A-Za-z0-9-]+/)?([0-9a-fA-F]{20,64})/?', url)
    if not match or not re.fullmatch(r'[0-9a-fA-F]{40}', revision):
        raise ValueError('Use a gist.github.com URL and a full 40-character revision SHA.')
    return match.group(1).lower(), revision.lower()


def fetch(url, revision):
    gist_id, revision = parse_source(url, revision)
    result = subprocess.run(['curl', '--disable', '--fail', '--silent', '--show-error', '--proto', '=https',
                             '--connect-timeout', '15', '--max-time', '60', '--max-filesize', '1048576',
                             '--header', 'Accept: application/vnd.github+json',
                             '--url', f'https://api.github.com/gists/{gist_id}/{revision}'],
                            check=True, capture_output=True)
    if len(result.stdout) > 1048576:
        raise ValueError('Gist response exceeds 1 MiB.')
    response = json.loads(result.stdout)
    if not isinstance(response, dict):
        raise ValueError('Expected a GitHub gist response object.')
    response_id = response.get('id')
    if not isinstance(response_id, str) or response_id.lower() != gist_id or response.get('truncated'):
        raise ValueError('Gist response is mismatched or truncated.')
    history = response.get('history', [])
    if (not isinstance(history, list) or not history or not isinstance(history[0], dict) or
            not isinstance(history[0].get('version'), str) or history[0]['version'].lower() != revision):
        raise ValueError('Gist response does not match the requested revision.')
    entries = response.get('files', {})
    if not isinstance(entries, dict) or not all(name in entries for name in FILES[:2]):
        raise ValueError('Gist must contain zshrc.shared and gitconfig.shared.')
    files = {}
    for name in FILES:
        if name not in entries:
            continue
        item = entries[name]
        if not isinstance(item, dict):
            raise ValueError(f'Invalid gist file entry: {name}')
        content = item.get('content')
        if (item.get('filename') != name or item.get('truncated') or not isinstance(content, str) or
                item.get('encoding', 'utf-8') != 'utf-8'):
            raise ValueError(f'Missing or truncated gist content: {name}')
        data = content.encode('utf-8')
        if b'\0' in data or len(data) > 262144:
            raise ValueError(f'Invalid or oversized dotfile: {name}')
        files[name] = data
    # Omission of the optional early layer explicitly clears a previously
    # installed early layer, subject to the same replacement/backup policy.
    files.setdefault('zshrc.shared.pre', b'# No shared pre-initialization settings.\n')
    return files


def validate(files):
    with tempfile.TemporaryDirectory(prefix='worker-dotfiles-') as temporary:
        for name, data in files.items():
            path = Path(temporary) / name
            path.write_bytes(data)
            command = ['/bin/zsh', '-dfn', str(path)] if name == '.zshrc' or name.startswith('zshrc.') else [
                'git', 'config', '--file', str(path), '--no-includes', '--list']
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise ValueError(f'Invalid syntax in {name}; no shared files were changed.')
            if name in ('.gitconfig', 'gitconfig.shared') and 'url.git@github.com:.insteadof=https://github.com/' in result.stdout.splitlines():
                raise ValueError('Shared Git config would restore the legacy GitHub HTTPS-to-SSH rewrite.')


def occurrences(text, block):
    # Comments or substrings of other commands are not active worker hooks.
    return list(re.finditer(r'(?m)^' + re.escape(block), text))


def add_before(text, line, anchor, label):
    lines, anchors = occurrences(text, line), occurrences(text, anchor)
    if len(lines) == 1 and len(anchors) == 1 and lines[0].start() < anchors[0].start():
        return text
    if line.strip() in text or len(anchors) != 1:
        raise ValueError(f'Ambiguous {label} layout; add the shared hook before the local override manually.')
    offset = anchors[0].start()
    return text[:offset] + line + '\n' + text[offset:]


def hook_plans(home):
    plans = {}
    for name in ('.zshrc', '.gitconfig'):
        target = destination(home, name)
        if target.is_symlink() or not target.is_file():
            raise ValueError(f'Hook migration requires a regular {target}; it will not replace a symlink.')
        text = target.read_text()
        if not text.endswith('\n'):
            text += '\n'
        if name == '.zshrc':
            local_hooks = occurrences(text, LOCAL)
            if len(local_hooks) != 1 or any(line.strip() and not line.lstrip().startswith('#')
                                          for line in text[local_hooks[0].end():].splitlines()):
                raise ValueError('Ambiguous .zshrc: expected the worker .zshrc.local hook last.')
            for hook, anchor in ((EARLY, 'typeset -U path fpath\n'), (LATE, LOCAL)):
                if hook not in text and '.config/worker/' + ('zshrc.shared.pre' if hook == EARLY else 'zshrc.shared"') in text:
                    raise ValueError('Unrecognized shared Zsh hook; review it before migration.')
                text = add_before(text, hook, anchor, '.zshrc')
        else:
            local_hooks = occurrences(text, GIT_LOCAL)
            if len(local_hooks) != 1 or any(line.strip() and not line.lstrip().startswith(('#', ';'))
                                          for line in text[local_hooks[0].end():].splitlines()):
                raise ValueError('Ambiguous .gitconfig: expected the worker .gitconfig.local include last.')
            if GIT_SHARED not in text and '.config/worker/gitconfig.shared' in text:
                raise ValueError('Unrecognized shared Git include; review it before migration.')
            text = add_before(text, GIT_SHARED, GIT_LOCAL, '.gitconfig')
        plans[name] = text.encode()
    return plans


def setup(home, url, revision, replace=False):
    gist_id, revision = parse_source(url, revision)
    files = fetch(url, revision)
    validate(files)
    hooks = hook_plans(home)  # Validate both hooks before installing either.
    validate(hooks)
    entries = [('.config/worker/' + name, data, 0o600, replace) for name, data in files.items()]
    # Selecting a gist explicitly opts into this narrow, backed-up hook migration.
    entries.extend((name, data, 0o600, True) for name, data in hooks.items())
    receipt = {'gist': gist_id, 'revision': revision,
               'files': {name: digest(data) for name, data in files.items()}}
    entries.append(('.local/state/worker/dotfiles.json',
                    (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode(), 0o600, True))
    install_many(home, entries, preserve_group=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', required=True)
    parser.add_argument('--gist', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--replace-config', action='store_true')
    args = parser.parse_args()
    try:
        setup(args.home, args.gist, args.revision, args.replace_config)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Error: Shared dotfiles: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
