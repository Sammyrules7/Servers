import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'setup_clis', Path(__file__).with_name('setup-clis.py'))
setup_clis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_clis)


class GitConfiguration(unittest.TestCase):
    def configure(self):
        """Run configure_git and return what it ran and what it removed."""
        commands, unsets = [], []

        def record(command, **kwargs):
            commands.append(command)

        def record_unset(command, **kwargs):
            unsets.append(command)
            return subprocess.CompletedProcess(command, 5)

        with patch.object(setup_clis, 'run', side_effect=record), \
                patch.object(setup_clis.subprocess, 'run', side_effect=record_unset):
            setup_clis.configure_git()
        return commands, unsets

    def test_scopes_the_credential_helper_to_the_public_host(self):
        """Git only asks this helper for the host T3 and every pull request link
        agree on, and the helper must not leak the token to any other host."""
        commands, _ = self.configure()
        helpers = [command for command in commands if 'helper' in command[3]]
        self.assertEqual(len(helpers), 1)
        self.assertEqual(helpers[0][3],
                         f'credential.https://{setup_clis.FORGEJO_HOST}.helper')
        self.assertTrue(helpers[0][4].startswith('!'))
        self.assertIn(str(setup_clis.TOKEN_DIRECTORY / 'forgejo-token'), helpers[0][4])

    def test_leaves_the_remote_url_alone(self):
        """T3 keys a repository by `git remote get-url` and compares it with the
        host on each pull request link, so nothing may rewrite the host away."""
        commands, _ = self.configure()
        written = ' '.join(' '.join(command) for command in commands)
        self.assertNotIn('insteadOf', written)
        self.assertNotIn(setup_clis.LEGACY_CLUSTER_HOST, written)

    def test_retires_keys_an_earlier_revision_wrote(self):
        """Homes that already configured the rewrite converge on removal."""
        _, unsets = self.configure()
        self.assertEqual(unsets, [['git', 'config', '--global', '--unset-all', key]
                                  for key in setup_clis.STALE_GIT_KEYS])
        self.assertTrue(any('insteadOf' in key for key in setup_clis.STALE_GIT_KEYS))


class ForgejoProvisioning(unittest.TestCase):
    def configure(self, logins='[]'):
        commands = []

        def record(command, **kwargs):
            commands.append((command, kwargs))

        def record_tea(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout=logins, stderr='')

        with patch.object(setup_clis, 'run', side_effect=record), \
                patch.object(setup_clis.subprocess, 'run', side_effect=record_tea):
            setup_clis.forgejo('secret-token')
        return commands

    def test_registers_both_clis_against_the_public_host(self):
        commands = self.configure()
        self.assertEqual([command for command, _ in commands], [
            ['fj', 'auth', 'add-token'],
            ['tea', 'login', 'add', '--name', 'maio-tech', '--no-version-check'],
            ['tea', 'login', 'default', 'maio-tech'],
        ])
        fj = commands[0][1]
        self.assertEqual(fj['input'], 'secret-token\n')
        tea = next(kwargs for command, kwargs in commands if command[2] == 'add')
        self.assertEqual(tea['env']['GITEA_SERVER_URL'],
                         f'https://{setup_clis.FORGEJO_HOST}')
        self.assertEqual(tea['env']['GITEA_SERVER_TOKEN'], 'secret-token')

    def test_replaces_an_existing_tea_login(self):
        commands = self.configure(logins='[{"name": "maio-tech"}]')
        self.assertIn(['tea', 'login', 'delete', 'maio-tech'],
                      [command for command, _ in commands])

    def test_revision_bump_invalidates_stored_marker(self):
        """A configuration change must reconfigure an already-provisioned pod."""
        token = 'secret-token'
        current = setup_clis.credential_digest(token)
        with patch.object(setup_clis, 'CONFIG_REVISION', setup_clis.CONFIG_REVISION + 1):
            self.assertNotEqual(setup_clis.credential_digest(token), current)
        self.assertEqual(current,
                         hashlib.sha256(f'{setup_clis.CONFIG_REVISION}\0{token}'.encode()).hexdigest())


class Provisioning(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.object(setup_clis, 'TOKEN_DIRECTORY', self.root / 'tokens').start()
        patch.object(setup_clis.Path, 'home', return_value=self.root / 'home').start()
        self.tokens = self.root / 'tokens'
        self.tokens.mkdir()
        self.marker = self.root / 'home/.config/t3-cli-credentials/forgejo'

    def secret(self, token='secret-token'):
        path = self.tokens / 'forgejo-token'
        path.write_text(token)
        return path

    def test_missing_secret_is_skipped(self):
        configured = []
        setup_clis.initialize('forgejo', configured.append)
        self.assertEqual(configured, [])
        self.assertFalse(self.marker.exists())

    def test_empty_secret_is_an_error(self):
        self.secret('')
        with self.assertRaises(ValueError):
            setup_clis.initialize('forgejo', lambda token: None)

    def test_success_marks_the_credential(self):
        self.secret()
        configured = []
        setup_clis.initialize('forgejo', configured.append)
        self.assertEqual(configured, ['secret-token'])
        self.assertEqual(self.marker.read_text(),
                         setup_clis.credential_digest('secret-token'))
        self.assertEqual(self.marker.stat().st_mode & 0o777, 0o600)

    def test_matching_marker_skips_reconfiguration(self):
        self.secret()
        setup_clis.initialize('forgejo', lambda token: None)
        configured = []
        setup_clis.initialize('forgejo', configured.append)
        self.assertEqual(configured, [])

    def test_failure_is_retried_and_leaves_the_marker_absent(self):
        """A briefly unavailable Forgejo must not hold the pod in a crash loop;
        the next start retries because the marker is only written on success."""
        self.secret()
        attempts = []

        def failing(token):
            attempts.append(token)
            raise subprocess.CalledProcessError(1, ['fj', 'auth', 'add-token'])

        with patch.object(setup_clis.time, 'sleep'):
            setup_clis.initialize('forgejo', failing, attempts=3, delay=0)
        self.assertEqual(len(attempts), 3)
        self.assertFalse(self.marker.exists())


if __name__ == '__main__':
    unittest.main()
