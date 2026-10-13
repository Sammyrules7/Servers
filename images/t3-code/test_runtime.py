import base64
import hashlib
import io
import tarfile
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
        self.versions = {'t3': '1.0-nightly.1', '@openai/codex': '1.0.0', '@opencode/cli': '2.0.28'}
        self.lookup = patch.object(runtime.urllib.request, 'urlopen', side_effect=self.response).start()
        self.install = patch.object(runtime.subprocess, 'run', side_effect=self.fake_run).start()

    def fake_run(self, command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout='opencode v' + self.versions['@opencode/cli'] + '\n')

    def archive(self, name='package/bin/opencode'):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode='w:gz') as archive:
            member = tarfile.TarInfo(name)
            member.size = len(b'fake binary')
            archive.addfile(member, io.BytesIO(b'fake binary'))
        return output.getvalue()

    def response(self, url, **kwargs):
        if url == 'https://registry.npmjs.org/binary.tgz':
            return io.BytesIO(self.archive())
        if f'/{runtime.OPENCODE_PLATFORM}/' in url:
            return io.BytesIO(json.dumps({
                'version': self.versions['@opencode/cli'],
                'dist': {'tarball': 'https://registry.npmjs.org/binary.tgz',
                         'integrity': 'sha512-' + base64.b64encode(hashlib.sha512(self.archive()).digest()).decode()}
            }).encode())
        package = next(package for package in self.versions if f'/{package}/' in url)
        return io.BytesIO(json.dumps({'version': self.versions[package]}).encode())

    def test_opencode_tracks_stable_channel(self):
        runtime.refresh()
        urls = [call.args[0] for call in self.lookup.call_args_list]
        self.assertIn('https://registry.npmjs.org/@opencode/cli/latest', urls)
        self.assertNotIn('https://registry.npmjs.org/@opencode/cli/dev', urls)

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
        self.versions['@opencode/cli'] = '2.0.29'
        self.assertTrue(runtime.refresh())
        self.assertNotEqual(old, (self.root / 'current').resolve())
        commands = [call.args[0] for call in self.install.call_args_list]
        self.assertIn('--ignore-scripts', commands[0])
        self.assertFalse(any('opencode' in argument for argument in commands[0]))
        self.assertEqual(['t3', 'codex', 'opencode'], [Path(c[0]).name for c in commands[1:]])
        self.assertTrue((self.root / 'current/node_modules/.bin/opencode').is_file())
        self.assertEqual(self.versions, json.loads((self.root / 'current/versions.json').read_text()))

    def test_opencode_validation_failure_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        previous = (old / 'versions.json').read_text()
        self.versions['@opencode/cli'] = '2.0.29'
        def fail(command, **kwargs):
            if Path(command[0]).name == 'opencode':
                raise subprocess.CalledProcessError(1, command)
            return self.fake_run(command, **kwargs)
        self.install.side_effect = fail
        with self.assertRaises(subprocess.CalledProcessError):
            runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())
        self.assertEqual(previous, (old / 'versions.json').read_text())
        self.assertEqual([old], list(self.root.glob('release-*')))

    def test_missing_opencode_binary_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        self.versions['@opencode/cli'] = '2.0.29'
        with patch.object(self, 'archive', side_effect=lambda: AtomicUpdates.archive(self, 'package/unexpected')):
            with self.assertRaises(KeyError):
                runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())
        self.assertEqual([old], list(self.root.glob('release-*')))

    def test_corrupt_archive_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        self.versions['@opencode/cli'] = '2.0.29'
        response = self.response
        self.lookup.side_effect = lambda url, **kw: io.BytesIO(b'corrupt') if url.endswith('/binary.tgz') else response(url, **kw)
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())
        self.assertEqual([old], list(self.root.glob('release-*')))

    def test_wrong_executable_version_preserves_old_release(self):
        runtime.refresh()
        old = (self.root / 'current').resolve()
        self.versions['@opencode/cli'] = '2.0.29'
        self.install.side_effect = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, stdout='0.0.0-dev-1')
        with self.assertRaisesRegex(ValueError, 'executable version'):
            runtime.refresh()
        self.assertEqual(old, (self.root / 'current').resolve())

    def test_dev_and_incompatible_releases_are_rejected_before_install(self):
        for version in ['0.0.0-dev-1', '1.19.0', '2.0.17', '2.0.28-beta.1']:
            self.versions['@opencode/cli'] = version
            with self.assertRaisesRegex(ValueError, 'requires stable OpenCode'):
                runtime.refresh()
        self.install.assert_not_called()

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
