"""Portable setup tests use fake downloads/builds and real syntax parsers only."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import unittest

import test_worker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import custom_workflow
import dotfiles
from worker_files import install

GIST = 'https://gist.github.com/example/' + 'a' * 32
REVISION = 'b' * 40


class PortableSetupTests(unittest.TestCase):
    run_worker = test_worker.WorkerTests.run_worker
    commands = test_worker.WorkerTests.commands
    assert_read_only_commands = test_worker.WorkerTests.assert_read_only_commands

    def setUp(self):
        test_worker.WorkerTests.setUp(self)
        self.archives = self.base / 'archives'; self.archives.mkdir()
        for name, module in [('ctx', 'github.com/goliatone/ctx'),
                             ('go-gql-gen', 'github.com/goliatone/go-gql-gen'), ('g', 'github.com/voidint/g')]:
            files = {'repo/go.mod': f'module {module}\n'}
            if name == 'ctx':
                files['repo/internal/ctxassets/defaults/assets/zsh/_ctx'] = '#compdef ctx\n_ctx() { :; }\n'
            self.write_archive(name, files)
        self.env['WORKER_TEST_ARCHIVES'] = str(self.archives)
        self.gist_file = self.base / 'gist.json'
        self.env['WORKER_TEST_GIST'] = str(self.gist_file)
        self.response = {'id': 'a' * 32, 'history': [{'version': REVISION}], 'files': {}}
        for name, content in [('zshrc.shared', 'export WORKER_LAYER=shared\n'),
                              ('zshrc.shared.pre', 'ZSH_THEME=shared-theme\n'),
                              ('gitconfig.shared', '[user]\n  name = Shared\n')]:
            self.response['files'][name] = {'filename': name, 'truncated': False, 'content': content}
        self.write_gist()

    def write_archive(self, name, files):
        with tarfile.open(self.archives / (name + '.tar.gz'), 'w:gz') as stream:
            for path, text in files.items():
                data = text.encode()
                member = tarfile.TarInfo(path); member.size = len(data)
                stream.addfile(member, io.BytesIO(data))

    def write_gist(self):
        self.gist_file.write_text(json.dumps(self.response))

    def base_configs(self):
        zsh = (ROOT / 'config/zsh/zshrc').read_text().replace(dotfiles.EARLY + '\n', '').replace(dotfiles.LATE + '\n', '')
        git = (ROOT / 'config/git/gitconfig').read_text().replace(dotfiles.GIT_SHARED + '\n', '')
        (self.home / '.zshrc').write_text(zsh)
        (self.home / '.gitconfig').write_text(git)

    def snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.home.rglob('*') if p.is_file() and not p.is_symlink()}

    def helper(self, name, *args, expected=0, **extra):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / name), '--home', str(self.home), *args],
                                cwd=self.base, env={**self.env, **extra}, text=True, capture_output=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def apply_gist(self, *args, **extra):
        return self.helper('dotfiles.py', '--gist', GIST, '--revision', REVISION, *args, **extra)

    def workflow(self, *args, **extra):
        return self.helper('install-workflow.py', '--root', str(ROOT), '--arch', 'arm64', *args, **extra)

    def test_all_new_options_dry_run_has_no_writes(self):
        result = self.run_worker('--dry-run', '--with-workflow', '--with-agents', '--with-backend',
                                 '--with-access', '--with-desktop', '--dotfiles-gist', GIST,
                                 '--dotfiles-revision', REVISION)
        for name in ('workflow', 'agents', 'backend', 'access', 'desktop'):
            self.assertIn('Brewfile.' + name, result.stdout)
        self.assertIn('No remote contents', result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.state.iterdir()), [])
        self.assert_read_only_commands()

    def test_value_options_and_platforms_fail_before_mutations(self):
        for args, expected in [(('--dotfiles-gist',), 2), (('--dotfiles-revision',), 2),
                                (('--dotfiles-gist', '--with-agents'), 2),
                                (('--dotfiles-gist', GIST), 1),
                                (('--dotfiles-revision', REVISION), 1),
                                (('--dotfiles-gist', 'https://evil.example/' + 'a' * 32, '--dotfiles-revision', REVISION), 1)]:
            with self.subTest(args=args):
                self.log.write_text('')
                self.run_worker(*args, expected=expected)
                self.assertEqual(self.commands(), [])
        self.run_worker('--with-desktop', expected=1, WORKER_TEST_MACOS_VERSION='13.7')
        self.run_worker('--with-access', expected=1, WORKER_TEST_MACOS_VERSION='12.7')
        self.assertFalse(any(s.startswith('brew ') for s in self.commands()))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_selected_bundle_failure_stops_before_configuration(self):
        self.run_worker('--with-backend', '--skip-extensions', expected=12, WORKER_TEST_FAIL_BUNDLE='backend')
        self.assertEqual(list(self.home.iterdir()), [])
        self.run_worker('--with-backend', '--skip-extensions', '--skip-macos')
        self.assertFalse(any('services start' in s or s.startswith(('open ', 'sudo ')) for s in self.commands()))

    def test_all_bundles_apply_rerun_and_dry_run(self):
        flags = ('--with-workflow', '--with-agents', '--with-backend', '--with-access', '--with-desktop', '--skip-extensions')
        self.run_worker(*flags)
        before = self.snapshot()
        self.log.write_text('')
        self.run_worker(*flags)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(any(s.startswith(('go install ', 'go build ', 'gh api ', 'curl ', 'defaults write ')) for s in self.commands()), self.commands())
        self.log.write_text('')
        self.run_worker(*flags, '--dry-run', '--replace-config')
        self.assertEqual(before, self.snapshot())
        self.assert_read_only_commands()
        self.assertTrue((self.home / '.agents/skills/ctx/SKILL.md').exists())
        self.assertTrue((self.home / '.claude/skills/ctx/SKILL.md').exists())
        self.assertTrue((self.home / 'Library/Application Support/iTerm2/DynamicProfiles/worker.json').exists())

    def test_gist_migration_backup_and_unchanged_rerun(self):
        self.base_configs()
        originals = self.snapshot()
        self.apply_gist()
        zsh = (self.home / '.zshrc').read_text()
        self.assertLess(zsh.index(dotfiles.EARLY), zsh.index('source "$ZSH/oh-my-zsh.sh"'))
        self.assertLess(zsh.index(dotfiles.LATE), zsh.index(dotfiles.LOCAL))
        backups = list((self.home / '.local/state/worker/backups').glob('config.*'))
        self.assertEqual(len(backups), 2)
        for backup in backups:
            target = Path((backup / 'destination.txt').read_text().strip())
            self.assertEqual((backup / target.name).read_bytes(), originals[target.name][0])
        before = self.snapshot()
        self.apply_gist()
        self.assertEqual(before, self.snapshot())
        self.assertEqual((self.home / '.zshrc').read_text().count(dotfiles.LATE), 1)

    def test_shared_configuration_precedence_in_real_zsh_and_git(self):
        self.base_configs()
        self.apply_gist()
        (self.home / '.zshrc.local').write_text('export WORKER_LAYER=local\n')
        (self.home / '.gitconfig.local').write_text('[user]\nname = Local\n')
        zsh = self.base / 'isolated.zshrc'
        zsh.write_text((self.home / '.zshrc').read_text().replace('$HOME', '$WORKER_HOME'))
        script = '''
compdef() { :; }
source() {
  case "$1" in
    "$WORKER_HOME/.config/worker/"*|"$WORKER_HOME/.zshrc.local") builtin source "$1" ;;
  esac
}
builtin source "$1"
[[ "$WORKER_LAYER" == local && "$ZSH_THEME" == shared-theme ]]
'''
        result = subprocess.run(['/bin/zsh', '-dfc', script, 'worker-test', str(zsh)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        git = self.base / 'isolated.gitconfig'
        git.write_text((self.home / '.gitconfig').read_text().replace('~/', str(self.home) + '/'))
        result = subprocess.run(['/usr/bin/git', 'config', '--file', str(git), '--includes', '--get', 'user.name'], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), 'Local')

    def test_invalid_remote_files_do_not_change_any_configs(self):
        self.base_configs()
        before = self.snapshot()
        original = json.loads(json.dumps(self.response))
        mutations = [lambda x: x.update(truncated=True), lambda x: x['history'][0].update(version='c' * 40),
                     lambda x: x['files'].pop('gitconfig.shared'),
                     lambda x: x['files']['zshrc.shared'].update(truncated=True),
                     lambda x: x['files']['zshrc.shared'].update(content='if then\n'),
                     lambda x: x['files']['gitconfig.shared'].update(content='[bad\n'),
                     lambda x: x['files']['gitconfig.shared'].update(content='[url "git@github.com:"]\ninsteadOf = https://github.com/\n')]
        for mutate in mutations:
            self.response = json.loads(json.dumps(original)); mutate(self.response); self.write_gist()
            self.apply_gist(expected=1)
            self.assertEqual(before, self.snapshot())
        self.apply_gist(expected=1, WORKER_TEST_FAIL_CURL='1')
        self.assertEqual(before, self.snapshot())

    def test_ambiguous_or_symlinked_hooks_are_preserved(self):
        self.base_configs()
        (self.home / '.zshrc').write_text('export CUSTOM=1\n')
        before = self.snapshot()
        self.apply_gist(expected=1)
        self.assertEqual(before, self.snapshot())
        self.base_configs()
        target = self.base / 'external.zshrc'
        (self.home / '.zshrc').rename(target)
        (self.home / '.zshrc').symlink_to(target)
        original = target.read_bytes()
        self.apply_gist(expected=1)
        self.assertTrue((self.home / '.zshrc').is_symlink())
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse((self.home / '.config/worker').exists())

    def test_gist_replacement_is_explicit_and_clears_removed_early_layer(self):
        self.base_configs(); self.apply_gist()
        self.response['files']['zshrc.shared']['content'] = 'export WORKER_LAYER=updated\n'
        self.response['files'].pop('zshrc.shared.pre')
        self.write_gist()
        before = self.snapshot()
        self.apply_gist()
        self.assertEqual(before, self.snapshot())
        self.apply_gist('--replace-config')
        self.assertIn('updated', (self.home / '.config/worker/zshrc.shared').read_text())
        self.assertNotIn('shared-theme', (self.home / '.config/worker/zshrc.shared.pre').read_text())
        self.assertTrue(any((p / 'zshrc.shared').exists() for p in (self.home / '.local/state/worker/backups').iterdir()))

    def test_gist_content_is_never_executed_during_installation(self):
        self.base_configs()
        sentinel = self.base / 'must-not-exist'
        self.response['files']['zshrc.shared']['content'] = 'touch "' + str(sentinel) + '"\n'
        self.write_gist(); self.apply_gist()
        self.assertFalse(sentinel.exists())

    def test_executable_backups_and_destination_symlinks(self):
        target = self.home / 'bin/helper'; target.parent.mkdir()
        external = self.base / 'external'; external.write_bytes(b'original')
        target.symlink_to(external)
        self.assertFalse(install(self.home, 'bin/helper', b'new', mode=0o700))
        self.assertTrue(install(self.home, 'bin/helper', b'new', mode=0o700, replace=True))
        self.assertEqual(external.read_bytes(), b'original')
        self.assertTrue(os.access(target, os.X_OK))
        backups = list((self.home / '.local/state/worker/backups').glob('*/helper'))
        self.assertEqual(len(backups), 1); self.assertTrue(backups[0].is_symlink())
        outside = self.base / 'outside'; outside.mkdir()
        (self.home / '.config').symlink_to(outside)
        with self.assertRaises(ValueError):
            install(self.home, '.config/worker/test', b'no')
        self.assertEqual(list(outside.iterdir()), [])

    def test_workflow_authentication_defers_private_builds(self):
        result = self.workflow(expected=2, WORKER_TEST_NO_AUTH='1')
        self.assertIn('ctx deferred', result.stdout)
        self.assertIn('gengql deferred', result.stdout)
        self.assertTrue((self.home / 'bin/g').exists())
        self.assertFalse((self.home / 'go/bin/ctx').exists())
        self.log.write_text('')
        self.workflow()
        self.assertTrue((self.home / 'go/bin/ctx').exists())
        self.assertFalse(any(s.startswith('curl ') for s in self.commands()))

    def test_captured_wrapper_forwards_arguments_to_the_selected_cli(self):
        cli = self.base / 'fixture ctx'
        cli.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n'); cli.chmod(0o700)
        result = subprocess.run(['/bin/bash', str(ROOT / 'config/workflow/ctx.sh'), '--help', 'argument with spaces'],
                                cwd=self.base, env={**self.env, 'CTX_CLI_BIN': str(cli)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['--help', 'argument with spaces'])

    def test_workflow_build_failure_keeps_custom_binary_and_retry_backs_it_up(self):
        target = self.home / 'go/bin/ctx'; target.parent.mkdir(parents=True)
        target.write_bytes(b'custom build'); target.chmod(0o700)
        self.workflow('--replace-config', expected=1, WORKER_TEST_FAIL_GO_BUILD='github.com/goliatone/ctx')
        self.assertEqual(target.read_bytes(), b'custom build')
        self.assertFalse((self.home / '.local/state/worker/backups').exists())
        self.workflow('--replace-config')
        backups = list((self.home / '.local/state/worker/backups').glob('*/ctx'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b'custom build')
        self.assertTrue(os.access(target, os.X_OK))

    def test_workflow_download_failure_and_existing_binary_preservation(self):
        self.workflow(expected=1, WORKER_TEST_FAIL_ARCHIVE='ctx')
        self.assertFalse((self.home / 'go/bin/ctx').exists())
        target = self.home / 'go/bin/ctx'; target.parent.mkdir(parents=True)
        target.write_bytes(b'custom build'); target.chmod(0o700)
        self.workflow(expected=2)
        self.assertEqual(target.read_bytes(), b'custom build')
        self.assertFalse((self.home / '.local/state/worker/tools/ctx.json').exists())

    def test_unsafe_source_archives_never_escape_staging(self):
        self.write_archive('bad', {'repo/../../escaped': 'no'})
        with self.assertRaises(ValueError):
            custom_workflow.extract(self.archives / 'bad.tar.gz', self.base / 'extract')
        self.assertFalse((self.base / 'escaped').exists())

    def test_agents_preserve_settings_and_exclude_runtime_credentials(self):
        config = self.home / '.codex/config.toml'; config.parent.mkdir()
        config.write_text('model = "keep-existing"\n')
        self.helper('install-agents.py', '--root', str(ROOT))
        self.assertEqual(config.read_text(), 'model = "keep-existing"\n')
        for path in (self.home / '.agents/skills').rglob('*'):
            self.assertNotIn('.ctx', path.relative_to(self.home / '.agents/skills').parts)
        for path in (self.home / '.codex/auth.json', self.home / '.claude/.credentials.json', self.home / '.ssh'):
            self.assertFalse(path.exists())
        self.helper('install-agents.py', '--root', str(ROOT), '--replace-config')
        self.assertEqual(config.read_bytes(), (ROOT / 'config/agents/codex.toml').read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
