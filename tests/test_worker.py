"""Installer regression tests. Only fixtures are written; external installers are fake."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = '/bin/bash'

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='worker tests ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'user home'
        self.home.mkdir()
        self.prefix = self.base / 'brew'
        bin_dir = self.prefix / 'bin'
        bin_dir.mkdir(parents=True)
        self.state = self.base / 'state'; self.state.mkdir()
        self.log = self.base / 'commands.log'; self.log.touch()
        fake = '#!' + sys.executable + '\n' + (ROOT / 'tests/fake-command.py').read_text().split('\n', 1)[1]
        for name in ['uname', 'sysctl', 'xcode-select', 'brew', 'git', 'npm', 'node', 'go', 'gh', 'code-insiders', 'defaults', 'curl', 'sudo', 'chsh', 'killall', 'open']:
            p = bin_dir / name; p.write_text(fake); p.chmod(0o700)
        self.env = {**os.environ, 'PATH': str(bin_dir) + ':/usr/bin:/bin:/usr/sbin:/sbin',
                    'WORKER_HOME': str(self.home), 'WORKER_TEST_PREFIX': str(self.prefix),
                    'WORKER_TEST_STATE': str(self.state), 'WORKER_TEST_LOG': str(self.log),
                    'PYTHONDONTWRITEBYTECODE': '1'}
        self.env.pop('BASH_ENV', None)
        self.env.pop('ENV', None)

    def run_worker(self, *args, expected=0, repo=ROOT, **extra):
        result = subprocess.run([BASH, str(repo / 'make'), *args], cwd=self.base,
                                env={**self.env, **extra}, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def commands(self):
        return self.log.read_text().splitlines()

    def test_dry_run_has_no_writes_or_external_installer_calls(self):
        result = self.run_worker('--dry-run')
        self.assertIn('Nothing was changed', result.stdout)
        self.assertIn('AppleShowAllExtensions', result.stdout)
        self.assertIn('visual', (ROOT / 'extensions/Brewfile').read_text())
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertTrue(all(s.startswith('uname ') for s in self.commands()), self.commands())
        self.assertEqual(list(self.state.iterdir()), [])

    def test_dry_run_does_not_source_existing_nvm_or_private_hooks(self):
        nvm = self.home / '.nvm'; nvm.mkdir()
        (nvm / 'nvm.sh').write_text('echo MUST_NOT_RUN >&2; exit 91\n')
        (self.home / '.zshrc').write_text('echo MUST_NOT_RUN >&2; exit 92\n')
        result = self.run_worker('--dry-run', '--replace-config')
        self.assertNotIn('MUST_NOT_RUN', result.stdout + result.stderr)
        self.assertFalse((self.home / '.local').exists())

    def test_apply_twice_keeps_files_tools_and_extensions(self):
        self.run_worker()
        first = self.commands()
        files = {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.home.rglob('*') if p.is_file()}
        self.log.write_text('')
        self.run_worker()
        second = self.commands()
        self.assertEqual(files, {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                                for p in self.home.rglob('*') if p.is_file()})
        self.assertEqual(sum(s.startswith('code-insiders --install-extension ') for s in first), 80)
        self.assertTrue(any('openai.chatgpt --pre-release' in s for s in first))
        for prefix in ['git clone ', 'go install ', 'npm install ', 'nvm install ', 'gh extension install ', 'code-insiders --install-extension ', 'defaults write ']:
            self.assertFalse(any(s.startswith(prefix) for s in second), prefix + '\n' + '\n'.join(second))
        self.assertFalse((self.home / '.local/state/worker/backups').exists())

    def test_existing_configs_preserved_unless_replacement_requested(self):
        target = self.home / '.gitconfig'; target.write_text('# personal\n')
        result = self.run_worker('--skip-extensions', '--skip-macos')
        self.assertEqual(target.read_text(), '# personal\n')
        self.assertIn('Preserved', result.stderr)
        self.run_worker('--replace-config', '--skip-extensions', '--skip-macos')
        self.assertEqual(target.read_bytes(), (ROOT / 'config/git/gitconfig').read_bytes())
        backups = list((self.home / '.local/state/worker/backups').glob('*/.gitconfig'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), '# personal\n')

    def test_symlink_replacement_does_not_touch_target(self):
        outside = self.base / 'elsewhere'; outside.mkdir()
        (outside / 'sentinel').write_text('untouched')
        target = self.home / '.gitconfig'; target.symlink_to(outside)
        self.run_worker('--replace-config', '--skip-extensions', '--skip-macos')
        self.assertFalse(target.is_symlink())
        self.assertEqual([p.name for p in outside.iterdir()], ['sentinel'])
        backups = list((self.home / '.local/state/worker/backups').glob('*/.gitconfig'))
        self.assertTrue(backups[0].is_symlink())
        self.assertEqual(backups[0].readlink(), outside)

    def test_stop_on_brew_failure(self):
        self.run_worker(expected=12, WORKER_TEST_FAIL_BREW='1')
        self.assertFalse(any(s.startswith(('git ', 'npm ', 'go ', 'defaults ')) for s in self.commands()))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_wrong_architecture_brew_is_rejected_before_installation(self):
        result = self.run_worker(expected=1, WORKER_TEST_REPORTED_PREFIX='/usr/local')
        self.assertIn('does not match', result.stderr)
        self.assertFalse(any(s.startswith('brew bundle ') for s in self.commands()))

    def test_nvm_failure_stops_following_modules(self):
        result = self.run_worker(expected=1, WORKER_TEST_FAIL_NVM='1')
        self.assertIn('Could not install Node LTS', result.stderr)
        self.assertFalse(any(s.startswith(('npm ', 'go ', 'defaults ')) for s in self.commands()))

    def test_old_node_default_cannot_install_incompatible_pnpm(self):
        (self.state / 'node-default').write_text('v16.20.2')
        result = self.run_worker(expected=1, WORKER_TEST_NODE_VERSION='v16.20.2')
        self.assertIn('18.12', result.stderr)
        self.assertFalse(any(s.startswith('npm install ') for s in self.commands()))

    def test_invalid_go_binary_is_repaired(self):
        binary = self.home / 'go/bin/gopls'
        binary.parent.mkdir(parents=True)
        binary.write_text('partial installation'); binary.chmod(0o700)
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertIn('@v0.23.0', binary.read_text())

    def test_wrong_architecture_go_binary_is_reinstalled(self):
        binary = self.home / 'go/bin/gopls'
        binary.parent.mkdir(parents=True)
        binary.write_text('golang.org/x/tools/gopls@v0.23.0'); binary.chmod(0o700)
        self.run_worker('--skip-extensions', '--skip-macos', WORKER_TEST_BINARY_ARCH='amd64')
        self.assertIn('go install golang.org/x/tools/gopls@v0.23.0', self.commands())

    def test_installers_cannot_consume_the_rest_of_a_manifest(self):
        self.run_worker(WORKER_TEST_CONSUME_STDIN='1')
        self.assertEqual(sum(s.startswith('go install ') for s in self.commands()), 4)
        self.assertEqual(sum(s.startswith('code-insiders --install-extension ') for s in self.commands()), 80)

    def test_manifests_without_final_newline(self):
        checkout = self.base / 'checkout with spaces'
        shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        for name in ['go-tools.txt', 'vscode-insiders.txt']:
            file = checkout / 'extensions' / name
            file.write_bytes(file.read_bytes().rstrip(b'\n'))
        self.run_worker(repo=checkout)
        self.assertEqual(sum(s.startswith('go install ') for s in self.commands()), 4)
        self.assertEqual(sum(s.startswith('code-insiders --install-extension ') for s in self.commands()), 80)

    def test_histdb_patch_applied_only_during_initial_clone(self):
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertTrue(any(' apply ' in s and 'zsh-histdb.patch' in s for s in self.commands()))
        self.log.write_text('')
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertFalse(any(' apply ' in s for s in self.commands()))

    def test_histdb_patch_failure_can_be_retried(self):
        self.run_worker('--skip-extensions', '--skip-macos', expected=1, WORKER_TEST_FAIL_PATCH='1')
        plugins = self.home / '.oh-my-zsh/custom/plugins'
        self.assertFalse((plugins / 'zsh-histdb').exists())
        self.assertFalse(list(plugins.glob('.worker-clone.*')))
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertTrue((plugins / 'zsh-histdb/sqlite-history.zsh').exists())

    def test_pnpm_path_present_before_directory_exists(self):
        pnpm_dir = self.base / 'not-yet-created-pnpm-home'
        # Evaluate the real snapshot in a child shell. Block all nested sources
        # so no real Oh My Zsh, NVM, completion, or private config can run.
        script = '''
compdef() { :; }
source() { :; }
builtin source "$WORKER_TEST_ZSHRC"
[[ "$PNPM_HOME" == "$WORKER_TEST_PNPM_HOME" ]] || exit 1
[[ ":$PATH:" == *":$PNPM_HOME:"* ]]
'''
        result = subprocess.run(['/bin/zsh', '-dfc', script], env={**self.env,
            'ZDOTDIR': str(self.base), 'PNPM_HOME': str(pnpm_dir),
            'WORKER_TEST_PNPM_HOME': str(pnpm_dir),
            'WORKER_TEST_ZSHRC': str(ROOT / 'config/zsh/zshrc')}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(pnpm_dir.exists())

    def test_missing_clt_requests_install_and_stops(self):
        result = self.run_worker(expected=1, WORKER_TEST_NO_CLT='1')
        self.assertIn('Complete the Command Line Tools', result.stderr)
        self.assertIn('xcode-select --install', self.commands())
        self.assertFalse(any(s.startswith('brew ') for s in self.commands()))

    def test_homebrew_bootstrap_and_download_failure_cleanup(self):
        # Run only the production brew module against a fake prefix. The curl
        # shim writes a tiny fixture installer that only copies our brew shim.
        brew = self.prefix / 'bin/brew'
        template = self.base / 'brew-template'
        shutil.copy2(brew, template)
        brew.unlink()
        script = '''
set -Eeuo pipefail
ROOT=$WORKER_TEST_ROOT
DRY_RUN=0
WORKER_LOADED=1
WARNINGS=0
BREW_PREFIX=$WORKER_TEST_PREFIX
source "$ROOT/utils.sh"
source "$ROOT/modules/brew.sh"
setup_brew
'''
        for mode in ['fail', 'installer-fail', 'success']:
            with self.subTest(mode=mode):
                self.log.write_text('')
                result = subprocess.run([BASH, '-c', script], env={**self.env,
                    'WORKER_TEST_ROOT': str(ROOT), 'WORKER_TEST_DOWNLOAD': mode,
                    'WORKER_TEST_BREW_TEMPLATE': str(template)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0 if mode == 'success' else 1, result.stdout + result.stderr)
                downloads = [s.rsplit(' -o ', 1)[1] for s in self.commands() if s.startswith('curl ')]
                self.assertEqual(len(downloads), 1)
                self.assertFalse(Path(downloads[0]).exists(), 'Downloaded script was not cleaned up')
                if mode != 'success':
                    self.assertFalse(brew.exists())
                    self.assertFalse(any(s.startswith('brew bundle ') for s in self.commands()))
        self.assertTrue(brew.exists())
        self.assertTrue(any(s.startswith('brew bundle install ') for s in self.commands()))

    def test_failed_checkout_leaves_no_partial_destination(self):
        self.run_worker(expected=1, WORKER_TEST_FAIL_CHECKOUT='1')
        self.assertFalse((self.home / '.nvm').exists())
        self.assertFalse(list(self.home.glob('.worker-clone.*')))
        self.run_worker('--skip-extensions', '--skip-macos')

    def test_auth_deferred_without_blocking_core_setup(self):
        result = self.run_worker('--skip-extensions', WORKER_TEST_NO_AUTH='1')
        self.assertIn('gh-dash deferred', result.stderr)
        self.assertTrue((self.home / '.zshrc').exists())
        self.assertFalse(any(s.startswith('gh extension install ') for s in self.commands()))

    def test_extension_failure_reported_and_retry_only_installs_missing(self):
        self.run_worker(expected=1, WORKER_TEST_FAIL_EXTENSION='golang.go')
        self.assertEqual(len(json.loads((self.state / 'extensions').read_text())), 79)
        self.assertFalse(any(s.startswith('defaults ') for s in self.commands()))
        self.log.write_text('')
        self.run_worker()
        installs = [s for s in self.commands() if s.startswith('code-insiders --install-extension ')]
        self.assertEqual(installs, ['code-insiders --install-extension golang.go'])

    def test_skip_flags(self):
        self.run_worker('--skip-macos', '--skip-extensions')
        self.assertFalse(any(s.startswith(('defaults ', 'code-insiders ')) for s in self.commands()))

    def test_argument_and_platform_guards(self):
        self.run_worker('--unknown', expected=2)
        self.run_worker('--dry-run', expected=1, WORKER_TEST_OS='Linux')
        self.run_worker('--dry-run', expected=1, WORKER_TEST_ARCH='x86_64', WORKER_TEST_ROSETTA='1')
        self.run_worker('--dry-run', WORKER_TEST_ARCH='x86_64')

    def test_snapshot_integrity(self):
        settings = json.loads((ROOT / 'config/vscode/settings.json').read_text())
        self.assertNotIn('sqltools.connections', settings)
        self.assertNotIn('go.goroot', settings)
        self.assertEqual(settings['go.lintTool'], 'golangci-lint-v2')
        for path in (ROOT / 'config').rglob('*'):
            if path.suffix in ['.json', '.code-snippets']:
                json.loads(path.read_text())
            if path.is_file():
                self.assertNotIn('/Users/goliatone', path.read_text(), str(path))
        result = subprocess.run(['/usr/bin/git', 'config', '--no-includes', '--file', str(ROOT / 'config/git/gitconfig'), '--name-only', '--get-regexp', '^alias\\.'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 28)
        result = subprocess.run(['/usr/bin/git', 'config', '--no-includes', '--file', str(ROOT / 'config/git/gitconfig'), '--get', 'difftool.vscode.cmd'], text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), 'code-insiders --wait --diff "$LOCAL" "$REMOTE"')

if __name__ == '__main__':
    unittest.main(verbosity=2)
