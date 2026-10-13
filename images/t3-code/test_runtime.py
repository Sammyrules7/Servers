import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import runtime


class AtomicUpdates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(runtime, 'RUNTIME', self.root).start()
        self.versions = {'t3': '1.0-nightly.1', '@openai/codex': '1.0.0', 'opencode-ai': '0.0.0-dev-1'}
        self.lookup = patch.object(runtime.urllib.request, 'urlopen', side_effect=self.response).start()
        self.install = patch.object(runtime.subprocess, 'run', side_effect=self.fake_run).start()

    def fake_run(self, command, **kwargs):
        if command[0] == 'npm':
            stage = Path(command[command.index('--prefix') + 1])
            binary = stage / 'node_modules/opencode-linux-x64-baseline/bin/opencode'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'fake binary')

    def response(self, url, **kwargs):
        package = next(package for package in self.versions if f'/{package}/' in url)
        return io.BytesIO(json.dumps({'version': self.versions[package]}).encode())

    def test_unchanged_channels_reuse_installation(self):
        self.assertTrue(runtime.refresh())
        installed = (self.root / 'current').resolve()
        self.install.reset_mock()
        self.assertFalse(runtime.refresh())
        self.install.assert_not_called()
        self.assertEqual(installed, (self.root / 'current').resolve())

    def test_failed_install_or_binary_check_keeps_previous_release(self):
        runtime.refresh()
        installed = (self.root / 'current').resolve()
        self.versions['t3'] = '1.0-nightly.2'
        for failure in (subprocess.CalledProcessError(1, 'npm'),
                        subprocess.TimeoutExpired('t3', 60)):
            self.install.side_effect = failure
            with self.assertRaises(type(failure)):
                runtime.refresh()
            self.assertEqual(installed, (self.root / 'current').resolve())
            self.assertEqual([installed], list(self.root.glob('release-*')))
        self.install.side_effect = lambda command, **kw: self.fake_run(command, **kw) if command[0] == 'npm' else (_ for _ in ()).throw(subprocess.CalledProcessError(1, 't3'))
        with self.assertRaises(subprocess.CalledProcessError):
            runtime.refresh()
        self.assertEqual(installed, (self.root / 'current').resolve())

    def test_opencode_only_change_validates_and_replaces(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        self.install.reset_mock()
        self.versions['opencode-ai'] = '0.0.0-dev-2'
        self.assertTrue(runtime.refresh())
        self.assertNotEqual(old, (self.root / 'current').resolve())
        commands = [call.args[0] for call in self.install.call_args_list]
        self.assertIn('--ignore-scripts', commands[0])
        self.assertIn('opencode-ai@0.0.0-dev-2', commands[0])
        self.assertIn('opencode-linux-x64-baseline@0.0.0-dev-2', commands[0])
        self.assertEqual(['t3', 'codex', 'opencode'], [Path(c[0]).name for c in commands[1:]])
        self.assertTrue((self.root / 'current/node_modules/.bin/opencode').is_file())
        self.assertEqual(self.versions, json.loads((self.root / 'current/versions.json').read_text()))

    def test_opencode_validation_failure_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        previous = (old / 'versions.json').read_text()
        self.versions['opencode-ai'] = '0.0.0-dev-2'
        def fail(command, **kwargs):
            if Path(command[0]).name == 'opencode':
                raise subprocess.CalledProcessError(1, command)
            self.fake_run(command, **kwargs)
        self.install.side_effect = fail
        with self.assertRaises(subprocess.CalledProcessError):
            runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())
        self.assertEqual(previous, (old / 'versions.json').read_text())
        self.assertEqual([old], list(self.root.glob('release-*')))

    def test_missing_opencode_binary_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        self.versions['opencode-ai'] = '0.0.0-dev-2'
        self.install.side_effect = None
        with self.assertRaises(FileNotFoundError):
            runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())
        self.assertEqual([old], list(self.root.glob('release-*')))

    def test_new_channel_versions_replace_installation_after_validation(self):
        runtime.refresh()
        installed = (self.root / 'current').resolve()
        self.versions['@openai/codex'] = '1.1.0'
        self.assertTrue(runtime.refresh())
        self.assertNotEqual(installed, (self.root / 'current').resolve())
        self.assertEqual(self.versions, json.loads((self.root / 'current/versions.json').read_text()))
        commands = [call.args[0] for call in self.install.call_args_list[-4:]]
        self.assertIn('@openai/codex@1.1.0', commands[0])
        self.assertEqual('--version', commands[1][-1])
        self.assertEqual('--version', commands[2][-1])


if __name__ == '__main__':
    unittest.main()
