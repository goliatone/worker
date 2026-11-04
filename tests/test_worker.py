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
        for name in ['uname', 'sysctl', 'sw_vers', 'xcode-select', 'brew', 'git', 'npm', 'node', 'go', 'gh', 'code-insiders', 'defaults', 'curl', 'sudo', 'chsh', 'killall', 'open']:
            p = bin_dir / name; p.write_text(fake); p.chmod(0o700)
        self.env = {**os.environ, 'PATH': str(bin_dir) + ':/usr/bin:/bin:/usr/sbin:/sbin',
                    'WORKER_HOME': str(self.home), 'WORKER_TEST_PREFIX': str(self.prefix),
                    'WORKER_TEST_STATE': str(self.state), 'WORKER_TEST_LOG': str(self.log),
                    'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(self.base)}
        self.env.pop('BASH_ENV', None)
        self.env.pop('ENV', None)

    def run_worker(self, *args, expected=0, repo=ROOT, **extra):
        result = subprocess.run([BASH, str(repo / 'make'), *args], cwd=self.base,
                                env={**self.env, **extra}, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def commands(self):
        return self.log.read_text().splitlines()

    def assert_read_only_commands(self):
        self.assertTrue(all(s.startswith('uname ') or s in ['xcode-select -p', 'sw_vers -productVersion'] or
                            (s.startswith('git config --file ') and
                             ' --no-includes --fixed-value --get-all ' in s)
                            for s in self.commands()), self.commands())

    def configure_git_rewrite(self):
        config = self.home / '.gitconfig'
        config.write_text('[url "git@github.com:"]\n\tinsteadOf = https://github.com/\n')
        self.env.update(GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM='1',
                        WORKER_TEST_GIT_CONFIG=str(config), WORKER_TEST_PUBLIC_GIT='1')
        # The fixture must reproduce the user's SSH rewrite before worker runs.
        result = subprocess.run(['/usr/bin/git', 'ls-remote', '--get-url',
                                 'https://github.com/deskflow/homebrew-tap'],
                                cwd=self.base, env=self.env, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), 'git@github.com:deskflow/homebrew-tap')
        return config

    def configure_public_git_snapshot(self):
        config = self.base / 'global.gitconfig'
        config.write_bytes((ROOT / 'config/git/gitconfig').read_bytes())
        # Keep the fixture from including the real user's private overrides.
        subprocess.run(['/usr/bin/git', 'config', '--file', str(config),
                        '--unset-all', 'include.path'], check=True)
        self.env.update(GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_NOSYSTEM='1',
                        WORKER_TEST_GIT_CONFIG=str(config), WORKER_TEST_PUBLIC_GIT='1')
        return config

    def test_captured_git_config_keeps_public_https_urls_on_reruns(self):
        config = self.configure_public_git_snapshot()
        original = config.read_bytes()
        for _ in range(2):
            self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos')
        self.assertEqual(config.read_bytes(), original)
        self.assertEqual(json.loads((self.state / 'public-git-urls').read_text()), [
            'https://github.com/Homebrew/homebrew-core', 'https://github.com/deskflow/homebrew-tap',
        ] * 2)

    def test_legacy_git_rewrite_repair_survives_homebrew_environment_filter(self):
        launcher = next((Path(p) for p in ['/opt/homebrew/bin/brew', '/usr/local/bin/brew']
                         if Path(p).is_file()), None)
        if launcher is None:
            self.skipTest('An installed Homebrew launcher is needed for this offline smoke test')
        config = self.configure_git_rewrite()
        config.write_text(config.read_text() + '[user]\n\tname = Keep Me\n'
                          '[url "git@github.com:"]\n\tinsteadOf = https://github.com/private-team/\n')
        # Run the real launcher/filter, replacing its downstream package manager
        # with an offline URL probe. Nothing in the installed Homebrew is run.
        checkout = self.base / 'launcher only'
        (checkout / 'bin').mkdir(parents=True)
        shutil.copy2(launcher, checkout / 'bin/brew')
        library = checkout / 'Library/Homebrew'
        library.mkdir(parents=True)
        (library / 'brew.sh').write_text('''#!/bin/bash
printf '%s\\n' "${GIT_CONFIG_GLOBAL-unset}" "${GIT_CONFIG_NOSYSTEM-unset}"
# Model the default global config after Homebrew's actual environment filter.
export GIT_CONFIG_GLOBAL="$HOMEBREW_WORKER_TEST_CONFIG" GIT_CONFIG_NOSYSTEM=1
exec /usr/bin/git ls-remote --get-url https://github.com/deskflow/homebrew-tap
''')
        def probe():
            env = {key: value for key, value in self.env.items() if not key.startswith('HOMEBREW_')}
            env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                       HOMEBREW_WORKER_TEST_CONFIG=str(config), XDG_CONFIG_HOME=str(self.base / 'xdg'))
            result = subprocess.run([str(checkout / 'bin/brew'), 'bundle', 'install'],
                                    cwd=self.base, env=env, text=True, capture_output=True, check=True)
            return result.stdout.splitlines()
        before = probe()
        self.assertEqual(before[-1], 'git@github.com:deskflow/homebrew-tap')
        if '/usr/bin/env -i' in launcher.read_text():
            self.assertEqual(before[:2], ['unset', 'unset'])
        self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos')
        self.assertEqual(probe()[-1], 'https://github.com/deskflow/homebrew-tap')
        self.assertIn('name = Keep Me', config.read_text())
        self.assertIn('insteadOf = https://github.com/private-team/', config.read_text())

    def test_legacy_git_repair_dry_run_backup_and_rerun(self):
        config = self.configure_git_rewrite()
        config.write_text(config.read_text() + '\tinsteadOf = https://github.com/\n'
                          '\tinsteadOf = https://github.com/private-team/\n'
                          '[user]\n\tname = Keep Me\n# Preserve this comment.\n')
        config.chmod(0o640)
        original = (config.read_bytes(), config.stat().st_mtime_ns)
        result = self.run_worker('--dry-run', '--with-deskflow')
        self.assertIn('Would back up', result.stdout)
        self.assertIn('remove only url.git@github.com:.insteadOf', result.stdout)
        self.assertEqual((config.read_bytes(), config.stat().st_mtime_ns), original)
        self.assertEqual(list(self.home.iterdir()), [config])
        self.assertEqual(list(self.state.iterdir()), [])
        self.assert_read_only_commands()
        self.log.write_text('')
        # Also works when the old workaround is still passed on the command line.
        self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos',
                        GIT_CONFIG_GLOBAL='/dev/null', WORKER_TEST_PUBLIC_GIT='')
        commands = self.commands()
        repair = next(i for i, s in enumerate(commands) if ' --unset-all ' in s)
        self.assertLess(repair, next(i for i, s in enumerate(commands) if s.startswith('brew ')))
        backups = list((self.home / '.local/state/worker/backups').glob('git-url-rewrite.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '.gitconfig').read_bytes(), original[0])
        self.assertEqual((backups[0] / 'destination.txt').read_text(), str(config) + '\n')
        self.assertEqual(config.stat().st_mode & 0o777, 0o640)
        self.assertIn('name = Keep Me', config.read_text())
        self.assertIn('# Preserve this comment.', config.read_text())
        self.assertIn('insteadOf = https://github.com/private-team/', config.read_text())
        self.assertNotIn('insteadOf = https://github.com/\n', config.read_text())
        repaired = (config.read_bytes(), config.stat().st_mtime_ns)
        self.log.write_text('')
        self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos')
        self.assertEqual((config.read_bytes(), config.stat().st_mtime_ns), repaired)
        self.assertEqual(list(backups[0].parent.iterdir()), backups)
        self.assertFalse(any(' --unset-all ' in s for s in self.commands()))

    def test_legacy_git_repair_preserves_nonmatching_rules_and_includes(self):
        included = self.home / 'included.gitconfig'
        included.write_text('[url "git@github.com:"]\n\tinsteadOf = https://github.com/\n')
        config = self.home / '.gitconfig'
        config.write_text('[url "git@github.com:"]\n\tinsteadOf = https://github.com/private-team/\n'
                          '[url "ssh://git@github.com/"]\n\tinsteadOf = https://github.com/\n'
                          '[include]\n\tpath = "' + str(included) + '"\n')
        before = {p: p.read_bytes() for p in (config, included)}
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertFalse((self.home / '.local/state/worker/backups').exists())

    def test_legacy_git_repair_dry_run_without_clt(self):
        config = self.configure_git_rewrite()
        original = config.read_bytes()
        result = self.run_worker('--dry-run', '--with-deskflow', WORKER_TEST_NO_CLT='1')
        self.assertIn('after Command Line Tools are installed', result.stdout)
        self.assertFalse(any(s.startswith('git ') for s in self.commands()))
        self.assertEqual(config.read_bytes(), original)
        self.assertEqual(list(self.home.iterdir()), [config])
        self.assert_read_only_commands()

    def test_legacy_git_repair_failures_stop_before_homebrew(self):
        config = self.configure_git_rewrite()
        original = config.read_bytes()
        for failure in ['backup', 'git-write', 'locked', 'symlink', 'malformed']:
            with self.subTest(failure=failure):
                self.log.write_text('')
                extra = {}
                if failure == 'backup':
                    (self.home / '.local').write_text('prevent backup directory creation')
                elif failure == 'git-write':
                    extra['WORKER_TEST_FAIL_GIT_REPAIR'] = '1'
                elif failure == 'locked':
                    (self.home / '.gitconfig.lock').write_text('another writer')
                elif failure == 'symlink':
                    target = self.base / 'linked.gitconfig'
                    config.rename(target)
                    config.symlink_to(target)
                else:
                    config.write_text('[invalid\n')
                before = config.read_bytes()
                self.run_worker('--with-deskflow', expected=1, **extra)
                self.assertEqual(config.read_bytes(), before)
                self.assertFalse(any(s.startswith(('brew ', 'curl ')) for s in self.commands()))
                if failure == 'backup':
                    (self.home / '.local').unlink()
                elif failure == 'locked':
                    lock = self.home / '.gitconfig.lock'
                    self.assertEqual(lock.read_text(), 'another writer')
                    lock.unlink()
                elif failure == 'symlink':
                    self.assertTrue(config.is_symlink())
                    config.unlink()
                    target.rename(config)
                elif failure == 'malformed':
                    config.write_bytes(original)

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

    def test_optional_deskflow_dry_run_does_not_invoke_homebrew(self):
        default = self.run_worker('--dry-run')
        self.assertNotIn('Brewfile.deskflow', default.stdout)
        selected = self.run_worker('--dry-run', '--with-deskflow')
        self.assertIn('Brewfile.deskflow', selected.stdout)
        self.assertIn('deskflow/tap', selected.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.state.iterdir()), [])
        self.assertTrue(all(s.startswith('uname ') for s in self.commands()), self.commands())

    def test_optional_deskflow_failure_and_retry(self):
        self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos',
                        expected=12, WORKER_TEST_FAIL_DESKFLOW='1')
        self.assertTrue(any(s.endswith('/Brewfile.deskflow') for s in self.commands()))
        self.assertFalse(any(s.startswith(('git ', 'npm ', 'go ', 'defaults ')) for s in self.commands()))
        self.assertEqual(list(self.home.iterdir()), [])
        self.log.write_text('')
        self.run_worker('--with-deskflow', '--skip-extensions', '--skip-macos')
        self.assertTrue(any(s.endswith('/Brewfile.deskflow') for s in self.commands()))
        self.assertTrue((self.home / '.zshrc').exists())
        self.log.write_text('')
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertFalse(any('Brewfile.deskflow' in s for s in self.commands()))

    def test_optional_ai_dry_run_and_alias(self):
        default = self.run_worker('--dry-run')
        self.assertNotIn('Brewfile.ai', default.stdout)
        for flags in [('--with-ai',), ('--ai',), ('--ai', '--with-ai', '--with-deskflow')]:
            with self.subTest(flags=flags):
                result = self.run_worker('--dry-run', *flags)
                self.assertEqual(result.stdout.count('/Brewfile.ai'), 1)
                for app in ['Ollama', 'LM Studio', 'Bionic', 'Unsloth Desktop']:
                    self.assertIn(app, result.stdout)
                self.assertEqual(list(self.home.iterdir()), [])
                self.assertEqual(list(self.state.iterdir()), [])
                self.assert_read_only_commands()

    def test_optional_ai_failure_and_retry(self):
        self.run_worker('--ai', '--with-deskflow', '--skip-extensions', '--skip-macos',
                        expected=12, WORKER_TEST_FAIL_AI='1')
        self.assertTrue(any(s.endswith('/Brewfile.ai') for s in self.commands()))
        self.assertFalse(any(s.startswith(('git ', 'npm ', 'go ', 'defaults ')) for s in self.commands()))
        self.assertEqual(list(self.home.iterdir()), [])
        self.log.write_text('')
        self.run_worker('--ai', '--with-ai', '--with-deskflow', '--skip-extensions', '--skip-macos')
        self.assertEqual(sum(s.endswith('/Brewfile.ai') for s in self.commands()), 1)
        self.assertTrue(any(s.endswith('/Brewfile.deskflow') for s in self.commands()))
        self.assertTrue((self.home / '.zshrc').exists())
        self.log.write_text('')
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertFalse(any('Brewfile.ai' in s for s in self.commands()))

    def test_optional_ai_requires_supported_mac_before_any_changes(self):
        for flags in [('--ai',), ('--dry-run', '--with-ai')]:
            for overrides, message in [({'WORKER_TEST_ARCH': 'x86_64'}, 'requires Apple Silicon'),
                                       ({'WORKER_TEST_MACOS_VERSION': '13.7.8'}, 'requires macOS 14'),
                                       ({'WORKER_TEST_MACOS_VERSION': 'unknown'}, 'Could not determine')]:
                with self.subTest(flags=flags, overrides=overrides):
                    self.log.write_text('')
                    result = self.run_worker(*flags, expected=1, **overrides)
                    self.assertIn(message, result.stderr)
                    self.assertTrue(all(s.startswith(('uname ', 'sysctl ', 'sw_vers ')) for s in self.commands()), self.commands())
                    self.assertEqual(list(self.home.iterdir()), [])
                    self.assertEqual(list(self.state.iterdir()), [])

    def test_bundle_cleanup_settings_cannot_override_worker(self):
        for setting in ('HOMEBREW_BUNDLE_INSTALL_CLEANUP', 'HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP'):
            with self.subTest(setting=setting):
                self.run_worker('--with-deskflow', '--with-ai', '--skip-extensions', '--skip-macos', **{setting: '1'})

    def test_selected_brewfiles_must_exist_before_any_installation(self):
        checkout = self.base / 'checkout with spaces'
        shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        for name, selection in [('Brewfile', []), ('Brewfile.deskflow', ['--with-deskflow']),
                                ('Brewfile.ai', ['--with-ai']),
                                *[('Brewfile.' + name, ['--with-' + name])
                                  for name in ('workflow', 'agents', 'backend', 'access', 'desktop')]]:
            manifest = checkout / 'extensions' / name
            original = manifest.read_bytes()
            manifest.unlink()
            for mode in [[], ['--dry-run']]:
                with self.subTest(manifest=name, mode=mode):
                    self.log.write_text('')
                    result = self.run_worker(*mode, *selection, repo=checkout, expected=1)
                    self.assertIn('Missing or unreadable Brewfile:', result.stderr)
                    self.assertIn(name, result.stderr)
                    self.assertTrue(all(s.startswith('uname ') for s in self.commands()), self.commands())
                    self.assertEqual(list(self.home.iterdir()), [])
                    self.assertEqual(list(self.state.iterdir()), [])
            if name != 'Brewfile':
                self.run_worker('--dry-run', repo=checkout)
            manifest.write_bytes(original)

    def test_optional_apps_dry_run_after_setup_is_read_only(self):
        self.run_worker('--with-deskflow', '--with-ai', '--skip-extensions')
        def snapshot():
            return {str(p.relative_to(self.base)): (p.read_bytes(), p.stat().st_mtime_ns)
                    for root in (self.home, self.state) for p in root.rglob('*') if p.is_file()}
        before = snapshot()
        self.log.write_text('')
        result = self.run_worker('--dry-run', '--replace-config', '--with-deskflow', '--with-ai')
        self.assertIn('Amphetamine', result.stdout)
        self.assertIn('Brewfile.deskflow', result.stdout)
        self.assertIn('Brewfile.ai', result.stdout)
        self.assertEqual(before, snapshot())
        self.assert_read_only_commands()
        self.log.write_text('')
        self.run_worker('--with-deskflow', '--with-ai', '--skip-extensions')
        self.assertEqual(before, snapshot())

    def test_apply_twice_keeps_files_tools_and_extensions(self):
        self.run_worker()
        first = self.commands()
        self.assertFalse(any('Brewfile.deskflow' in s for s in first))
        self.assertFalse(any('Brewfile.ai' in s for s in first))
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
        config = self.configure_public_git_snapshot()
        original_config = config.read_bytes()
        brew = self.prefix / 'bin/brew'
        template = self.base / 'brew-template'
        shutil.copy2(brew, template)
        brew.unlink()
        taps = self.base / 'bootstrap-taps.txt'
        taps.write_text('github.com/example/homebrew-bootstrap\n')
        script = '''
set -Eeuo pipefail
ROOT=$WORKER_TEST_ROOT
DRY_RUN=0
WORKER_LOADED=1
WARNINGS=0
BREW_PREFIX=$WORKER_TEST_PREFIX
TAPS_FILE=$WORKER_TEST_TAPS
source "$ROOT/utils.sh"
source "$ROOT/modules/taps.sh"
load_custom_taps
source "$ROOT/modules/brew.sh"
setup_brew
'''
        for mode in ['fail', 'installer-fail', 'success']:
            with self.subTest(mode=mode):
                self.log.write_text('')
                result = subprocess.run([BASH, '-c', script], env={**self.env,
                    'WORKER_TEST_ROOT': str(ROOT), 'WORKER_TEST_DOWNLOAD': mode,
                    'WORKER_TEST_TAPS': str(taps),
                    'WORKER_TEST_BREW_TEMPLATE': str(template)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0 if mode == 'success' else 1, result.stdout + result.stderr)
                downloads = [s.rsplit(' -o ', 1)[1] for s in self.commands() if s.startswith('curl ')]
                self.assertEqual(len(downloads), 1)
                self.assertFalse(Path(downloads[0]).exists(), 'Downloaded script was not cleaned up')
                if mode != 'success':
                    self.assertFalse(brew.exists())
                    self.assertFalse(any(s.startswith('brew bundle ') for s in self.commands()))
        self.assertTrue(brew.exists())
        self.assertIn('brew tap example/bootstrap https://github.com/example/homebrew-bootstrap', self.commands())
        self.assertTrue(any(s.startswith('brew bundle install ') for s in self.commands()))
        self.assertEqual(config.read_bytes(), original_config)

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
