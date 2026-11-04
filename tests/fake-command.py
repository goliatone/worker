#!/usr/bin/env python3
"""No network or host changes: stand-ins for every installer external command."""
import json
import os
from pathlib import Path
import subprocess
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

def tap_directory(tap):
    owner, repository = tap.split('/')
    assert all(part and '/' not in part and part not in ('.', '..') for part in (owner, repository))
    return Path(os.environ['WORKER_TEST_PREFIX']) / 'Library/Taps' / owner / ('homebrew-' + repository)

if name == 'uname':
    print(os.environ.get('WORKER_TEST_ARCH', 'arm64') if args == ['-m'] else os.environ.get('WORKER_TEST_OS', 'Darwin'))
elif name == 'sysctl':
    print(os.environ.get('WORKER_TEST_ROSETTA', '0'))
elif name == 'sw_vers':
    assert args == ['-productVersion']
    print(os.environ.get('WORKER_TEST_MACOS_VERSION', '14.0'))
elif name == 'xcode-select':
    if args == ['-p']:
        sys.exit(1 if os.environ.get('WORKER_TEST_NO_CLT') else 0)
elif name == 'brew':
    if args == ['--prefix']:
        print(os.environ.get('WORKER_TEST_REPORTED_PREFIX', os.environ['WORKER_TEST_PREFIX']))
    elif args == ['tap']:
        if os.environ.get('WORKER_TEST_FAIL_TAP_LIST'):
            sys.exit(23)
        base = Path(os.environ['WORKER_TEST_PREFIX']) / 'Library/Taps'
        for path in sorted(base.glob('*/*')):
            # Homebrew's Tap.installed enumerates directories, even when a
            # checkout is incomplete or uses a .git pointer file.
            if path.is_dir():
                print(path.parent.name + '/' + path.name.removeprefix('homebrew-'))
    elif args[0] == '--repository':
        assert len(args) == 2
        print(tap_directory(args[1]))
    elif args[0] == 'tap':
        assert len(args) == 3 and not args[1].startswith('-'), args
        assert os.environ['HOMEBREW_NO_AUTO_UPDATE'] == '1'
        assert os.environ['HOMEBREW_NO_INSTALL_CLEANUP'] == '1'
        assert 'HOMEBREW_BUNDLE_INSTALL_CLEANUP' not in os.environ
        assert 'HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP' not in os.environ
        if args[1] == os.environ.get('WORKER_TEST_FAIL_TAP'):
            sys.exit(24)
        if os.environ.get('WORKER_TEST_CONSUME_STDIN'):
            sys.stdin.read()
        checkout = tap_directory(args[1])
        assert not checkout.exists(), 'An installed tap must be skipped'
        (checkout / '.git/objects').mkdir(parents=True)
        (checkout / '.git/refs').mkdir()
        (checkout / '.git/HEAD').write_text('ref: refs/heads/main\n')
        (checkout / '.git/config').write_text('[remote "origin"]\nurl = ' + args[2] + '\n')
    elif args[:2] == ['bundle', 'install']:
        assert '--no-upgrade' in args
        assert os.environ['HOMEBREW_NO_AUTO_UPDATE'] == '1'
        assert os.environ['HOMEBREW_NO_INSTALL_CLEANUP'] == '1'
        # Bundle cleanup removes packages absent from this Brewfile. The normal
        # install-cleanup setting above does not disable these separate switches.
        assert 'HOMEBREW_BUNDLE_INSTALL_CLEANUP' not in os.environ
        assert 'HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP' not in os.environ
        if os.environ.get('WORKER_TEST_PUBLIC_GIT'):
            url = 'https://github.com/deskflow/homebrew-tap' if any(
                arg.endswith('/Brewfile.deskflow') for arg in args) else 'https://github.com/Homebrew/homebrew-core'
            # Resolve offline after modeling Homebrew dropping GIT_* overrides
            # and Git reading its default global configuration.
            git_env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
            git_env.update(GIT_CONFIG_GLOBAL=os.environ['WORKER_TEST_GIT_CONFIG'], GIT_CONFIG_NOSYSTEM='1')
            resolved = subprocess.check_output(
                ['/usr/bin/git', 'ls-remote', '--get-url', url], cwd=state, env=git_env, text=True).strip()
            assert resolved == url, f'Public bootstrap URL rewritten: {resolved}'
            checked = load('public-git-urls', [])
            checked.append(resolved); save('public-git-urls', checked)
        if any(arg.endswith('/Brewfile.deskflow') for arg in args):
            sys.exit(12 if os.environ.get('WORKER_TEST_FAIL_DESKFLOW') else 0)
        if any(arg.endswith('/Brewfile.ai') for arg in args):
            sys.exit(12 if os.environ.get('WORKER_TEST_FAIL_AI') else 0)
        if any(arg.endswith('/Brewfile.' + os.environ.get('WORKER_TEST_FAIL_BUNDLE', 'missing')) for arg in args):
            sys.exit(12)
        sys.exit(12 if os.environ.get('WORKER_TEST_FAIL_BREW') else 0)
    else:
        assert args == ['analytics', 'off'], args
elif name == 'git':
    if args[0] == '-C' and args[2:] == ['config', '--local', '--includes', '--get-all', 'remote.origin.url']:
        Path(args[1]).resolve().relative_to(state.parent.resolve())
        sys.exit(subprocess.run(['/usr/bin/git', *args]).returncode)
    if args[:2] == ['config', '--file']:
        # Exercise Git's real parser/locking only against this test's fixtures.
        Path(args[2]).resolve().relative_to(state.parent.resolve())
        if args[-2:] == ['--no-includes', '--list']:
            sys.exit(subprocess.run(['/usr/bin/git', *args]).returncode)
        assert '--no-includes' in args and '--fixed-value' in args
        assert '--get-all' in args or '--unset-all' in args
        if '--unset-all' in args and os.environ.get('WORKER_TEST_FAIL_GIT_REPAIR'):
            sys.exit(23)
        sys.exit(subprocess.run(['/usr/bin/git', *args]).returncode)
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
        if 'worker-go-' in os.environ['GOBIN']:
            assert os.environ['GOFLAGS'] == ''
            assert os.environ['GIT_CONFIG_COUNT'] == '0'
            assert 'GIT_CONFIG_PARAMETERS' not in os.environ
        package = args[1]
        if package == os.environ.get('WORKER_TEST_FAIL_GO_INSTALL'):
            sys.exit(19)
        binary = package.split('@')[0].split('/')[-1]
        dest = Path(os.environ['GOBIN']) / binary
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(package); dest.chmod(0o700)
    elif args[0] == 'build':
        assert os.environ['GOOS'] == 'darwin'
        assert os.environ['GOWORK'] == 'off'
        assert os.environ['GOFLAGS'] == ''
        assert 'GIT_CONFIG_PARAMETERS' not in os.environ
        module = Path('go.mod').read_text().splitlines()[0].split()[1]
        assert os.environ['GIT_CONFIG_COUNT'] == ('1' if 'goliatone/' in module else '0')
        if module == os.environ.get('WORKER_TEST_FAIL_GO_BUILD'):
            sys.exit(19)
        package = module + (args[-1][1:] if args[-1] != '.' else '')
        dest = Path(args[args.index('-o') + 1])
        dest.write_text(package + '@(devel)'); dest.chmod(0o700)
    else:
        raise AssertionError(args)
elif name == 'gh':
    if os.environ.get('WORKER_TEST_PUBLIC_GIT'):
        assert os.environ.get('GIT_CONFIG_GLOBAL') == os.environ['WORKER_TEST_GIT_CONFIG']
    if args[:2] == ['auth', 'status']:
        sys.exit(1 if os.environ.get('WORKER_TEST_NO_AUTH') else 0)
    elif args == ['extension', 'list']:
        print('gh dash dlvhdr/gh-dash v4.0.0' if load('gh-dash') else '')
    elif args[:2] == ['extension', 'install']:
        save('gh-dash', True)
    elif args[0] == 'api' and '/tarball/' in args[1]:
        assert args[2:] == ['--hostname', 'github.com']
        repo = args[1].split('/')[2]
        if repo == os.environ.get('WORKER_TEST_FAIL_ARCHIVE'):
            sys.exit(22)
        sys.stdout.buffer.write((Path(os.environ['WORKER_TEST_ARCHIVES']) / (repo + '.tar.gz')).read_bytes())
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
        value = preferences[key]
        # macOS prints stored booleans as 1/0, not the true/false used to write.
        print(int(value) if isinstance(value, bool) else value)
    elif args[0] == 'write':
        assert len(args) == 5, args
        if args[3] == '-bool':
            if args[4].lower() not in ('true', 'false', 'yes', 'no'):
                print('defaults: -bool requires true, false, yes, or no', file=sys.stderr)
                sys.exit(255)
            value = args[4].lower() in ('true', 'yes')
        elif args[3] == '-string':
            value = args[4]
        else:
            raise AssertionError(args)
        if key == os.environ.get('WORKER_TEST_FAIL_PREFERENCE'):
            print('defaults: simulated write failure', file=sys.stderr)
            sys.exit(23)
        preferences[key] = value; save('preferences', preferences)
    else:
        raise AssertionError(args)
elif name == 'curl' and '--url' in args:
    assert args[0] == '--disable'
    url = args[args.index('--url') + 1]
    if os.environ.get('WORKER_TEST_FAIL_CURL'):
        sys.exit(22)
    if url.startswith('https://api.github.com/gists/'):
        sys.stdout.write(Path(os.environ['WORKER_TEST_GIST']).read_text())
    elif url.startswith('https://codeload.github.com/voidint/g/tar.gz/'):
        Path(args[args.index('-o') + 1]).write_bytes((Path(os.environ['WORKER_TEST_ARCHIVES']) / 'g.tar.gz').read_bytes())
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
if [[ -n "${WORKER_TEST_PUBLIC_GIT:-}" ]]; then
  resolved=$(/usr/bin/git ls-remote --get-url https://github.com/Homebrew/brew)
  [[ "$resolved" == https://github.com/Homebrew/brew ]] || exit 128
fi
cp "$WORKER_TEST_BREW_TEMPLATE" "$WORKER_TEST_PREFIX/bin/brew"
chmod 700 "$WORKER_TEST_PREFIX/bin/brew"
''')
else:
    # Real downloads and system changes must never run in these tests.
    raise AssertionError('Forbidden command: ' + name + ' ' + repr(args))
