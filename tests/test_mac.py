"""Preference regression tests; real defaults is limited to a temporary plist."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = '/bin/bash'


class MacPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='worker preferences ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin_dir = self.base / 'bin'; self.bin_dir.mkdir()
        self.state = self.base / 'state'; self.state.mkdir()
        self.log = self.base / 'commands.log'; self.log.touch()
        fake = '#!' + sys.executable + '\n' + (ROOT / 'tests/fake-command.py').read_text().split('\n', 1)[1]
        executable = self.bin_dir / 'defaults'
        executable.write_text(fake); executable.chmod(0o700)
        self.env = {**os.environ, 'PATH': str(self.bin_dir) + ':/usr/bin:/bin',
                    'WORKER_TEST_ROOT': str(ROOT), 'WORKER_TEST_STATE': str(self.state),
                    'WORKER_TEST_LOG': str(self.log), 'PYTHONDONTWRITEBYTECODE': '1'}
        self.env.pop('BASH_ENV', None)
        self.env.pop('ENV', None)

    def run_mac(self, script='setup_mac', *args, expected=0, dry_run=False, skip=False, **extra):
        bootstrap = '''
set -Eeuo pipefail
WORKER_LOADED=1
DRY_RUN=$WORKER_TEST_DRY_RUN
SKIP_MACOS=$WORKER_TEST_SKIP_MACOS
source "$WORKER_TEST_ROOT/utils.sh"
source "$WORKER_TEST_ROOT/modules/mac.sh"
'''
        result = subprocess.run([BASH, '-c', bootstrap + script, 'worker-mac-test', *args],
                                cwd=self.base, env={**self.env, **extra,
                                    'WORKER_TEST_DRY_RUN': str(int(dry_run)),
                                    'WORKER_TEST_SKIP_MACOS': str(int(skip))},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_setup_and_rerun_preserve_preference_types_and_mtime(self):
        self.run_mac()
        preferences = self.state / 'preferences'
        self.assertEqual(json.loads(preferences.read_text()), {
            'com.apple.finder/AppleShowAllFiles': True,
            'NSGlobalDomain/AppleShowAllExtensions': True,
            'com.apple.finder/FXPreferredViewStyle': 'clmv',
            'com.apple.finder/ShowStatusBar': True,
            'com.apple.dock/autohide': True,
        })
        writes = [line for line in self.log.read_text().splitlines() if line.startswith('defaults write ')]
        self.assertEqual(len(writes), 5)
        self.assertEqual(sum(line.endswith('-bool true') for line in writes), 4)
        before = (preferences.read_bytes(), preferences.stat().st_mtime_ns)
        self.log.write_text('')
        self.run_mac()
        self.assertNotIn('defaults write ', self.log.read_text())
        self.assertEqual(before, (preferences.read_bytes(), preferences.stat().st_mtime_ns))

    def test_boolean_readbacks_are_normalized(self):
        preferences = self.state / 'preferences'
        for desired, readings in [('true', [True, 1, 'true', 'TRUE', 'True', 'yes', 'YES', 'Yes']),
                                  ('false', [False, 0, 'false', 'FALSE', 'False', 'no', 'NO', 'No'])]:
            for current in readings:
                with self.subTest(desired=desired, current=current):
                    preferences.write_text(json.dumps({'test/Enabled': current}))
                    before = (preferences.read_bytes(), preferences.stat().st_mtime_ns)
                    self.log.write_text('')
                    self.run_mac('set_preference test Enabled -bool "$1"', desired)
                    self.assertNotIn('defaults write ', self.log.read_text())
                    self.assertEqual(before, (preferences.read_bytes(), preferences.stat().st_mtime_ns))

    def test_boolean_writes_use_text_and_correct_changed_values(self):
        preferences = self.state / 'preferences'
        for desired, value in [('1', True), ('true', True), ('YES', True), ('True', True),
                               ('0', False), ('false', False), ('NO', False), ('False', False)]:
            with self.subTest(desired=desired):
                preferences.write_text(json.dumps({'test/Enabled': not value}))
                self.log.write_text('')
                self.run_mac('set_preference test Enabled -bool "$1"', desired)
                self.assertIs(json.loads(preferences.read_text())['test/Enabled'], value)
                self.assertIn('defaults write test Enabled -bool ' + str(value).lower(), self.log.read_text())
        preferences.write_text(json.dumps({'test/Enabled': 'invalid'}))
        self.run_mac('set_preference test Enabled -bool false')
        self.assertIs(json.loads(preferences.read_text())['test/Enabled'], False)

    def test_invalid_boolean_input_stops_without_calling_defaults(self):
        for value in ('', '2', 'enabled'):
            with self.subTest(value=value):
                result = self.run_mac('set_preference test Enabled -bool "$1"', value, expected=1)
                self.assertIn('Invalid boolean preference', result.stderr)
                self.assertEqual(self.log.read_text(), '')
                self.assertEqual(list(self.state.iterdir()), [])

    def test_dry_run_has_valid_plan_and_never_calls_defaults(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.run_mac()
                before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.state.iterdir()}
                self.log.write_text('')
                result = self.run_mac(dry_run=True)
                self.assertEqual(result.stdout.count('-bool true'), 4)
                self.assertIn('-string clmv', result.stdout)
                self.assertEqual(self.log.read_text(), '')
                self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.state.iterdir()})

    def test_failed_write_stops_and_rerun_retries_remaining_preferences(self):
        result = self.run_mac(expected=1,
                              WORKER_TEST_FAIL_PREFERENCE='com.apple.finder/ShowStatusBar')
        self.assertIn('Could not set macOS preference: com.apple.finder ShowStatusBar', result.stderr)
        self.assertNotIn('com.apple.dock', self.log.read_text())
        self.assertEqual(len(json.loads((self.state / 'preferences').read_text())), 3)
        self.log.write_text('')
        self.run_mac()
        self.assertEqual([line for line in self.log.read_text().splitlines() if line.startswith('defaults write ')], [
            'defaults write com.apple.finder ShowStatusBar -bool true',
            'defaults write com.apple.dock autohide -bool true',
        ])

    def test_skip_macos_never_calls_defaults(self):
        self.run_mac(skip=True)
        self.assertEqual(self.log.read_text(), '')
        self.assertEqual(list(self.state.iterdir()), [])

    @unittest.skipUnless(sys.platform == 'darwin', 'Requires macOS defaults')
    def test_real_defaults_boolean_types_readback_and_reruns(self):
        # Only this absolute temporary file is passed to real defaults; never
        # call setup_mac here, which targets the user's Finder/Dock preferences.
        domain = self.base / 'disposable preferences'
        plist = domain.with_suffix('.plist')
        script = '''
defaults() {
  if [[ $1 == write ]]; then printf '%s\\n' "$*" >> "$WORKER_TEST_LOG"; fi
  /usr/bin/defaults "$@"
}
set_preference "$1" Enabled -bool "$2"
'''
        for value in (True, False):
            with self.subTest(value=value):
                self.run_mac(script, str(domain), str(value).lower())
                with plist.open('rb') as stream:
                    self.assertIs(plistlib.load(stream)['Enabled'], value)
                read = subprocess.run(['/usr/bin/defaults', 'read', str(domain), 'Enabled'],
                                      capture_output=True, text=True, check=True)
                self.assertEqual(read.stdout.strip(), '1' if value else '0')
                before = (plist.read_bytes(), plist.stat().st_mtime_ns)
                self.log.write_text('')
                self.run_mac(script, str(domain), str(value).lower())
                self.assertEqual(self.log.read_text(), '')
                self.assertEqual(before, (plist.read_bytes(), plist.stat().st_mtime_ns))


if __name__ == '__main__':
    unittest.main(verbosity=2)
