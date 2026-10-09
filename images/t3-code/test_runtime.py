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
        self.versions = {'t3': '1.0-nightly.1', '@openai/codex': '1.0.0'}
        self.lookup = patch.object(runtime.urllib.request, 'urlopen', side_effect=self.response).start()
        self.install = patch.object(runtime.subprocess, 'run').start()

    def response(self, url, **kwargs):
        package = 't3' if '/t3/' in url else '@openai/codex'
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
        self.install.side_effect = [None, subprocess.CalledProcessError(1, 't3')]
        with self.assertRaises(subprocess.CalledProcessError):
            runtime.refresh()
        self.assertEqual(installed, (self.root / 'current').resolve())

    def test_new_channel_versions_replace_installation_after_validation(self):
        runtime.refresh()
        installed = (self.root / 'current').resolve()
        self.versions['@openai/codex'] = '1.1.0'
        self.assertTrue(runtime.refresh())
        self.assertNotEqual(installed, (self.root / 'current').resolve())
        self.assertEqual(self.versions, json.loads((self.root / 'current/versions.json').read_text()))
        commands = [call.args[0] for call in self.install.call_args_list[-3:]]
        self.assertIn('@openai/codex@1.1.0', commands[0])
        self.assertEqual('--version', commands[1][-1])
        self.assertEqual('--version', commands[2][-1])


if __name__ == '__main__':
    unittest.main()
