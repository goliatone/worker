#!/usr/bin/env python3
"""No network or host changes: stand-ins for every installer external command."""
import json
import os
from pathlib import Path
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
state = Path(os.environ['WORKER_TEST_STATE'])
with Path(os.environ['WORKER_TEST_LOG']).open('a') as f:
    f.write(name + ' ' + ' '.join(args) + '\n')

def save(key, value):
    (state / key).write_text(json.dumps(value))

def load(key, default=None):
    p = state / key
    return json.loads(p.read_text()) if p.exists() else default

if name == 'uname':
    print(os.environ.get('WORKER_TEST_ARCH', 'arm64') if args == ['-m'] else os.environ.get('WORKER_TEST_OS', 'Darwin'))
elif name == 'sysctl':
    print(os.environ.get('WORKER_TEST_ROSETTA', '0'))
elif name == 'xcode-select':
    if args == ['-p']:
        sys.exit(1 if os.environ.get('WORKER_TEST_NO_CLT') else 0)
elif name == 'brew':
    if args == ['--prefix']:
        print(os.environ.get('WORKER_TEST_REPORTED_PREFIX', os.environ['WORKER_TEST_PREFIX']))
    elif args[:2] == ['bundle', 'install']:
        assert '--no-upgrade' in args
        assert os.environ['HOMEBREW_NO_AUTO_UPDATE'] == '1'
        assert os.environ['HOMEBREW_NO_INSTALL_CLEANUP'] == '1'
        # Bundle cleanup removes packages absent from this Brewfile. The normal
        # install-cleanup setting above does not disable these separate switches.
        assert 'HOMEBREW_BUNDLE_INSTALL_CLEANUP' not in os.environ
        assert 'HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP' not in os.environ
        if any(arg.endswith('/Brewfile.deskflow') for arg in args):
            sys.exit(12 if os.environ.get('WORKER_TEST_FAIL_DESKFLOW') else 0)
        sys.exit(12 if os.environ.get('WORKER_TEST_FAIL_BREW') else 0)
    else:
        assert args == ['analytics', 'off'], args
elif name == 'git':
    assert os.environ.get('GIT_CONFIG_GLOBAL') == '/dev/null'
    assert os.environ.get('GIT_CONFIG_NOSYSTEM') == '1'
    if args[0] == 'clone':
        dest = Path(args[-1]); dest.mkdir(exist_ok=True)
        if 'nvm-sh/nvm' in args[1]:
            (dest / 'nvm.sh').write_text('''nvm() {
  printf 'nvm %s\\n' "$*" >> "$WORKER_TEST_LOG"
  case "$1" in
    version) if [[ -f "$WORKER_TEST_STATE/node-default" ]]; then cat "$WORKER_TEST_STATE/node-default"; else echo N/A; return 3; fi ;;
    install) [[ -z "${WORKER_TEST_FAIL_NVM:-}" ]] || return 17; echo v26.0.0 > "$WORKER_TEST_STATE/node-installed" ;;
    alias) cp "$WORKER_TEST_STATE/node-installed" "$WORKER_TEST_STATE/node-default" ;;
    current) echo v26.0.0 ;;
    use) : ;;
    *) return 55 ;;
  esac
}
''')
        elif 'ohmyzsh/ohmyzsh' in args[1]:
            (dest / 'oh-my-zsh.sh').write_text('# fake dependency\n')
            (dest / 'custom/plugins').mkdir(parents=True)
        elif 'zsh-histdb' in args[1]:
            (dest / 'sqlite-history.zsh').write_text('# fake dependency\n')
        else:
            raise AssertionError(args)
    elif args[0] == '-C':
        if args[2] == 'apply':
            sys.exit(18 if os.environ.get('WORKER_TEST_FAIL_PATCH') else 0)
        sys.exit(13 if os.environ.get('WORKER_TEST_FAIL_CHECKOUT') else 0)
    else:
        raise AssertionError(args)
elif name == 'npm':
    if args[0] == 'list':
        print(json.dumps({'dependencies': {'pnpm': {'version': '10.32.1'}}} if load('pnpm') else {}))
    elif args[:2] == ['install', '--global']:
        save('pnpm', True)
    else:
        raise AssertionError(args)
elif name == 'node':
    if args == ['--version']:
        print(os.environ.get('WORKER_TEST_NODE_VERSION', 'v26.0.0'))
        sys.exit(0)
    data = json.load(sys.stdin)
    sys.exit(0 if data.get('dependencies', {}).get('pnpm', {}).get('version') else 1)
elif name == 'go':
    if args[:2] == ['version', '-m']:
        package = Path(args[2]).read_text()
        if '@' not in package:
            sys.exit(1)
        path, version = package.rsplit('@', 1)
        print('path\t' + path + '\nmod\t' + path + '\t' + version)
        print('build\tGOOS=darwin\nbuild\tGOARCH=' + os.environ.get('WORKER_TEST_BINARY_ARCH', 'arm64'))
    elif args[0] == 'install':
        if os.environ.get('WORKER_TEST_CONSUME_STDIN'): sys.stdin.read()
        assert os.environ.get('GOOS') == 'darwin'
        assert os.environ.get('GOARCH') == ('amd64' if os.environ.get('WORKER_TEST_ARCH') == 'x86_64' else 'arm64')
        package = args[1]
        binary = package.split('@')[0].split('/')[-1]
        dest = Path(os.environ['GOBIN']) / binary
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(package); dest.chmod(0o700)
    else:
        raise AssertionError(args)
elif name == 'gh':
    if args == ['auth', 'status']:
        sys.exit(1 if os.environ.get('WORKER_TEST_NO_AUTH') else 0)
    elif args == ['extension', 'list']:
        print('gh dash dlvhdr/gh-dash v4.0.0' if load('gh-dash') else '')
    elif args[:2] == ['extension', 'install']:
        save('gh-dash', True)
    else:
        raise AssertionError(args)
elif name == 'code-insiders':
    extensions = load('extensions', [])
    if args == ['--list-extensions']:
        print('\n'.join(extensions))
    elif args[0] == '--install-extension':
        if os.environ.get('WORKER_TEST_CONSUME_STDIN'): sys.stdin.read()
        if args[1] == os.environ.get('WORKER_TEST_FAIL_EXTENSION'):
            sys.exit(14)
        extensions.append(args[1]); save('extensions', extensions)
    else:
        raise AssertionError(args)
elif name == 'defaults':
    preferences = load('preferences', {})
    key = '/'.join(args[1:3])
    if args[0] == 'read':
        if key not in preferences: sys.exit(1)
        print(preferences[key])
    elif args[0] == 'write':
        preferences[key] = args[-1]; save('preferences', preferences)
    else:
        raise AssertionError(args)
elif name == 'curl' and os.environ.get('WORKER_TEST_DOWNLOAD'):
    mode = os.environ['WORKER_TEST_DOWNLOAD']
    if mode == 'fail': sys.exit(22)
    output = Path(args[args.index('-o') + 1])
    if mode == 'installer-fail':
        output.write_text('#!/bin/bash\nexit 23\n')
    else:
        output.write_text('''#!/bin/bash
set -e
cp "$WORKER_TEST_BREW_TEMPLATE" "$WORKER_TEST_PREFIX/bin/brew"
chmod 700 "$WORKER_TEST_PREFIX/bin/brew"
''')
else:
    # Real downloads and system changes must never run in these tests.
    raise AssertionError('Forbidden command: ' + name + ' ' + repr(args))
