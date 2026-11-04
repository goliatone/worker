"""Custom-tap integration tests: fake Homebrew, real Git reads in fixtures."""
import subprocess
import unittest

import test_worker


class CustomTapTests(unittest.TestCase):
    run_worker = test_worker.WorkerTests.run_worker
    commands = test_worker.WorkerTests.commands
    assert_read_only_commands = test_worker.WorkerTests.assert_read_only_commands

    def setUp(self):
        test_worker.WorkerTests.setUp(self)
        self.taps = self.base / 'custom taps.txt'

    def apply(self, *args, **kwargs):
        return self.run_worker('--skip-extensions', '--skip-macos', '--taps-file', str(self.taps), *args, **kwargs)

    def tap_path(self, name):
        owner, repository = name.split('/')
        return self.prefix / 'Library/Taps' / owner / ('homebrew-' + repository)

    def installed_tap(self, name, remote):
        checkout = self.tap_path(name)
        (checkout / '.git/objects').mkdir(parents=True, exist_ok=True)
        (checkout / '.git/refs').mkdir(exist_ok=True)
        (checkout / '.git/HEAD').write_text('ref: refs/heads/main\n')
        config = checkout / '.git/config'
        config.write_text('[remote "origin"]\nurl = ' + remote + '\n')
        return config

    def additions(self):
        return [line for line in self.commands() if line.startswith('brew tap ')]

    def home_snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.home.rglob('*') if p.is_file()}

    def test_argument_and_file_errors_precede_all_commands(self):
        for args, expected in [(('--taps-file',), 2), (('--taps-file', ''), 2),
                               (('--taps-file', '--dry-run'), 2),
                               (('--taps-file', str(self.taps)), 1),
                               (('--taps-file', str(self.base)), 1)]:
            with self.subTest(args=args):
                self.run_worker(*args, expected=expected)
                self.assertEqual(self.commands(), [])
                self.assertEqual(list(self.home.iterdir()), [])

    def test_entire_list_validated_before_mutations(self):
        invalid = ['http://github.com/example/homebrew-tools', 'git@github.com:example/homebrew-tools',
                   'https://github.com.evil/example/homebrew-tools', 'https://name:token@github.com/example/tools',
                   'https://github.com/example/tools/tree/main', 'https://github.com/example/tools?token=secret',
                   'https://github.com/example/tools#fragment', 'example/tools', '../other',
                   'github.com/example/homebrew-', 'github.com/example/homebrew-homebrew-tools',
                   'github.com/example/../tools', 'github.com/example/homebrew-tools $(touch sentinel)',
                   'github.com/example/homebrew-\0tools']
        for value in invalid:
            with self.subTest(value=value):
                self.taps.write_text('github.com/goliatone/homebrew-tap\n' + value + '\n')
                self.apply(expected=1)
                self.assertEqual(self.commands(), [])
                self.assertEqual(list(self.home.iterdir()), [])
                self.assertEqual(list(self.state.iterdir()), [])
                self.assertFalse((self.base / 'sentinel').exists())

    def test_list_collisions_fail_before_commands(self):
        self.taps.write_text('github.com/example/homebrew-tools\ngithub.com/example/tools\n')
        result = self.apply(expected=1)
        self.assertIn('Conflicting repository URLs', result.stderr)
        self.assertEqual(self.commands(), [])

    def test_dry_run_normalizes_deduplicates_and_never_queries_brew(self):
        self.taps.write_bytes(b'  # My taps\r\n\r\n \tGITHUB.COM/Goliatone/Homebrew-Tap.git/ \t\r\n'
                              b'https://github.com/goliatone/homebrew-tap\r\n'
                              b'github.com/goliatone/homebree-tap')
        result = self.apply('--dry-run')
        self.assertIn('tap goliatone/tap https://github.com/goliatone/homebrew-tap', result.stdout)
        self.assertIn('tap goliatone/homebree-tap https://github.com/goliatone/homebree-tap', result.stdout)
        self.assertEqual(result.stdout.count('tap goliatone/tap https://'), 1)
        self.assert_read_only_commands()
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.state.iterdir()), [])
        self.assertFalse((self.prefix / 'Library').exists())

    def test_apply_and_rerun_keep_existing_taps_and_files(self):
        self.taps.write_text('github.com/goliatone/homebrew-tap\nhttps://github.com/nats-io/homebrew-nats-tools\n')
        self.apply(WORKER_TEST_CONSUME_STDIN='1', HOMEBREW_BUNDLE_INSTALL_CLEANUP='1')
        self.assertEqual(self.additions(), [
            'brew tap goliatone/tap https://github.com/goliatone/homebrew-tap',
            'brew tap nats-io/nats-tools https://github.com/nats-io/homebrew-nats-tools'])
        commands = self.commands()
        self.assertLess(commands.index(self.additions()[-1]), next(i for i, line in enumerate(commands) if line.startswith('brew bundle ')))
        before = self.home_snapshot()
        configs = {name: (self.tap_path(name) / '.git/config').stat().st_mtime_ns
                   for name in ['goliatone/tap', 'nats-io/nats-tools']}
        self.log.write_text('')
        self.apply()
        self.assertEqual(self.additions(), [])
        self.assertEqual(before, self.home_snapshot())
        for name, mtime in configs.items():
            self.assertEqual((self.tap_path(name) / '.git/config').stat().st_mtime_ns, mtime)
        self.log.write_text('')
        self.apply('--dry-run', '--replace-config')
        self.assertEqual(before, self.home_snapshot())
        self.assert_read_only_commands()

    def test_equivalent_existing_https_and_ssh_urls_are_kept(self):
        self.taps.write_text('github.com/goliatone/homebrew-tap\n')
        for remote in ['https://github.com/Goliatone/Homebrew-Tap.git/',
                       'git@github.com:goliatone/homebrew-tap.git',
                       'ssh://git@github.com/goliatone/homebrew-tap']:
            with self.subTest(remote=remote):
                config = self.installed_tap('goliatone/tap', remote)
                before = (config.read_bytes(), config.stat().st_mtime_ns)
                self.log.write_text('')
                self.apply()
                self.assertEqual(self.additions(), [])
                self.assertEqual((config.read_bytes(), config.stat().st_mtime_ns), before)

    def test_origin_inspection_ignores_git_rewrites_and_caller_git_directory(self):
        self.taps.write_text('github.com/example/homebrew-tools\n')
        config = self.installed_tap('example/tools', 'https://github.com/example/homebrew-tools')
        global_config = self.base / 'caller.gitconfig'
        global_config.write_text('[url "ssh://wrong.example/"]\ninsteadOf = https://github.com/\n')
        self.apply(GIT_CONFIG_GLOBAL=str(global_config), GIT_DIR=str(self.base / 'missing.git'),
                   GIT_WORK_TREE=str(self.base), GIT_COMMON_DIR=str(self.base / 'missing.git'))
        self.assertEqual(self.additions(), [])
        self.assertIn('https://github.com/example/homebrew-tools', config.read_text())

    def test_custom_taps_combine_with_optional_bundles(self):
        self.taps.write_text('github.com/nats-io/homebrew-nats-tools\n')
        self.apply('--with-backend')
        self.assertEqual(self.additions(), ['brew tap nats-io/nats-tools https://github.com/nats-io/homebrew-nats-tools'])
        self.assertTrue(any(line.endswith('/Brewfile.backend') for line in self.commands()))
        self.log.write_text('')
        self.apply('--with-backend')
        self.assertEqual(self.additions(), [])

    def test_all_existing_origins_checked_before_any_addition(self):
        self.taps.write_text('github.com/example/homebrew-new\ngithub.com/goliatone/homebrew-tap\n')
        config = self.installed_tap('goliatone/tap', 'https://github.com/someone/other')
        before = config.read_bytes()
        result = self.apply(expected=1)
        self.assertIn('different repository', result.stderr)
        self.assertEqual(self.additions(), [])
        self.assertFalse(any(line.startswith('brew bundle ') for line in self.commands()))
        self.assertEqual(config.read_bytes(), before)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invalid_or_multiple_existing_origins_are_not_changed_or_exposed(self):
        self.taps.write_text('github.com/example/homebrew-tools\n')
        for remote in ['https://user:secret@github.com/example/homebrew-tools',
                       'https://github.com/example/homebrew-tools\nurl = https://github.com/other/tools',
                       'https://github.com/example/homebrew-tools\nurl =',
                       '\nurl = https://github.com/example/homebrew-tools',
                       '"https://github.com/example/homebrew-tools\\n"',
                       'github.com/example/homebrew-tools',
                       'GIT@github.com:example/homebrew-tools',
                       'ssh://GIT@github.com/example/homebrew-tools']:
            with self.subTest(remote=remote):
                config = self.installed_tap('example/tools', remote)
                before = config.read_bytes()
                self.log.write_text('')
                result = self.apply(expected=1)
                self.assertNotIn('secret', result.stdout + result.stderr)
                self.assertEqual(self.additions(), [])
                self.assertEqual(config.read_bytes(), before)

    def test_conflicting_included_origins_stop_before_any_additions(self):
        self.taps.write_text('github.com/example/homebrew-new\ngithub.com/example/homebrew-tools\n')
        config = self.installed_tap('example/tools', 'https://github.com/example/homebrew-tools')
        included = self.base / 'included.gitconfig'
        included.write_text('[remote "origin"]\nurl = https://github.com/other/homebrew-tools\n')
        config.write_text('[include]\npath = "' + str(included) + '"\n' + config.read_text())
        before = (config.read_bytes(), included.read_bytes())
        self.apply(expected=1)
        self.assertEqual(self.additions(), [])
        self.assertFalse(any(line.startswith('brew bundle ') for line in self.commands()))
        self.assertEqual(before, (config.read_bytes(), included.read_bytes()))

    def test_single_included_origin_and_git_pointer_file_are_supported(self):
        self.taps.write_text('github.com/example/homebrew-tools\n')
        config = self.installed_tap('example/tools', 'https://github.com/example/homebrew-tools')
        included = self.base / 'included.gitconfig'
        included.write_bytes(config.read_bytes())
        config.write_text('[include]\npath = "' + str(included) + '"\n')
        metadata = self.base / 'separate git directory'
        config.parent.rename(metadata)
        pointer = self.tap_path('example/tools') / '.git'
        pointer.write_text('gitdir: ' + str(metadata) + '\n')
        before = (pointer.read_bytes(), (metadata / 'config').read_bytes(), included.read_bytes())
        self.apply()
        self.assertEqual(self.additions(), [])
        self.assertEqual(before, (pointer.read_bytes(), (metadata / 'config').read_bytes(), included.read_bytes()))

    def test_incomplete_tap_does_not_read_the_parent_homebrew_origin(self):
        self.taps.write_text('github.com/example/homebrew-new\ngithub.com/Homebrew/brew\n')
        config = self.installed_tap('homebrew/brew', 'https://github.com/Homebrew/brew')
        config.parent.rename(self.prefix / '.git')
        # Git's normal discovery would find this unrelated parent origin.
        result = subprocess.run(['/usr/bin/git', '-C', str(self.tap_path('homebrew/brew')), 'config',
                                 '--local', '--get', 'remote.origin.url'], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), 'https://github.com/Homebrew/brew')
        result = self.apply(expected=1)
        self.assertIn('incomplete checkout', result.stderr)
        self.assertEqual(self.additions(), [])
        self.assertFalse(any(line.startswith('brew bundle ') for line in self.commands()))

    def test_origin_reader_ignores_inherited_git_config_selectors(self):
        config = self.installed_tap('example/tools', 'https://github.com/example/homebrew-tools')
        override = self.base / 'override.gitconfig'
        override.write_text('[remote "origin"]\nurl = https://github.com/other/repository\n')
        script = '''
set -euo pipefail
WORKER_LOADED=1
source "$WORKER_TEST_ROOT/modules/taps.sh"
custom_tap_origin_url "$WORKER_TEST_REPOSITORY"
'''
        for overrides in ({'GIT_CONFIG': str(override)}, {'GIT_CONFIG_COUNT': 'invalid'},
                          {'GIT_CONFIG_PARAMETERS': 'invalid'}):
            with self.subTest(overrides=overrides):
                result = subprocess.run(['/bin/bash', '-c', script], capture_output=True, text=True,
                                        env={**self.env, **overrides, 'WORKER_TEST_ROOT': str(test_worker.ROOT),
                                             'WORKER_TEST_REPOSITORY': str(config.parent.parent)})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), 'https://github.com/example/homebrew-tools')

    def test_failed_addition_retries_only_missing_taps(self):
        self.taps.write_text('github.com/example/homebrew-first\ngithub.com/example/homebrew-second\n')
        self.apply(expected=24, WORKER_TEST_FAIL_TAP='example/second')
        self.assertTrue(self.tap_path('example/first').is_dir())
        self.assertFalse(self.tap_path('example/second').exists())
        self.assertEqual(list(self.home.iterdir()), [])
        self.log.write_text('')
        self.apply()
        self.assertEqual(self.additions(), ['brew tap example/second https://github.com/example/homebrew-second'])

    def test_failed_inventory_does_not_add_taps_or_install_packages(self):
        self.taps.write_text('github.com/example/homebrew-tools\n')
        self.apply(expected=1, WORKER_TEST_FAIL_TAP_LIST='1')
        self.assertEqual(self.additions(), [])
        self.assertFalse(any(line.startswith('brew bundle ') for line in self.commands()))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_relative_path_and_empty_list_and_omitted_flag_preserve_taps(self):
        config = self.installed_tap('example/keep', 'https://github.com/example/homebrew-keep')
        before = config.read_bytes()
        self.taps.write_text('# No extra taps\n\n')
        self.run_worker('--dry-run', '--taps-file', self.taps.name)
        self.assert_read_only_commands()
        self.log.write_text('')
        self.apply()
        self.assertFalse(any(line.startswith('brew tap') for line in self.commands()))
        self.log.write_text('')
        self.taps.write_text('invalid content is ignored without the flag\n')
        self.run_worker('--skip-extensions', '--skip-macos')
        self.assertFalse(any(line.startswith('brew tap') for line in self.commands()))
        self.assertEqual(config.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
