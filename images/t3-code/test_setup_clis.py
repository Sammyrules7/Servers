import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'setup_clis', Path(__file__).with_name('setup-clis.py'))
setup_clis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_clis)


class ClusterLoginMerge(unittest.TestCase):
    def test_adds_cluster_host_and_keeps_aliases(self):
        """T3 matches its fj login against `git remote get-url`, which the
        insteadOf rewrite reports as the in-cluster host, so that host needs the
        token too. Merging must not disturb fj's SSH alias table."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            aliases = {'git.forgejo.maio-tech.com': setup_clis.FORGEJO_HOST}
            path.write_text(json.dumps({
                'hosts': {setup_clis.FORGEJO_HOST: {'type': 'Application', 'token': 'old'}},
                'aliases': aliases,
                'default_ssh': [],
            }))
            setup_clis.merge_cluster_login(path, 'secret-token')
            keys = json.loads(path.read_text())
            self.assertEqual(keys['aliases'], aliases)
            self.assertEqual(keys['hosts'][setup_clis.FORGEJO_HOST]['token'], 'old')
            self.assertEqual(keys['hosts'][setup_clis.FORGEJO_CLUSTER_HOST],
                             {'type': 'Application', 'token': 'secret-token'})

    def test_creates_store_when_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested' / 'keys.json'
            path.parent.mkdir()
            setup_clis.merge_cluster_login(path, 'secret-token')
            self.assertEqual(json.loads(path.read_text())['hosts'][setup_clis.FORGEJO_CLUSTER_HOST]['token'],
                             'secret-token')


class ForgejoProvisioning(unittest.TestCase):
    def test_public_login_uses_fj_and_cluster_login_is_merged(self):
        commands = []

        def record(command, **kwargs):
            commands.append(command)

        def record_tea(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout='[]', stderr='')

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keys.json'
            with patch.object(setup_clis, 'run', side_effect=record), \
                    patch.object(setup_clis.subprocess, 'run', side_effect=record_tea), \
                    patch.object(setup_clis, 'forgejo_keys_path', return_value=path):
                setup_clis.forgejo('secret-token')
            self.assertIn(['fj', 'auth', 'add-token'], commands)
            self.assertEqual(json.loads(path.read_text())['hosts'][setup_clis.FORGEJO_CLUSTER_HOST]['token'],
                             'secret-token')

    def test_revision_bump_invalidates_stored_marker(self):
        """A configuration change must reconfigure an already-provisioned pod."""
        token = 'secret-token'
        current = setup_clis.credential_digest(token)
        with patch.object(setup_clis, 'CONFIG_REVISION', setup_clis.CONFIG_REVISION + 1):
            self.assertNotEqual(setup_clis.credential_digest(token), current)
        self.assertEqual(current,
                         hashlib.sha256(f'{setup_clis.CONFIG_REVISION}\0{token}'.encode()).hexdigest())


if __name__ == '__main__':
    unittest.main()
