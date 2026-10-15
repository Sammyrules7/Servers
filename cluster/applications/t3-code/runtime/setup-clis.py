"""Initialize persisted CLI logins from projected secrets without logging tokens."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

FORGEJO_HOST = 'forgejo.maio-tech.com'
# The global url.<cluster>.insteadOf rewrite (below) makes `git remote get-url`
# report the in-cluster service. T3's Forgejo provider resolves a repository's
# server from that output and matches it against fj/tea logins, so the token
# must also be registered for this host or those logins never match.
FORGEJO_CLUSTER_HOST = 'forgejo-http.forgejo.svc.cluster.local:3000'
# Bump when the configuration commands change so already-provisioned pods
# reconfigure once instead of trusting a stale marker.
CONFIG_REVISION = 2


def run(command, **kwargs):
    return subprocess.run(command, check=True, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, **kwargs)


def credential_digest(token):
    return hashlib.sha256(f'{CONFIG_REVISION}\0{token}'.encode()).hexdigest()


def forgejo_keys_path():
    """fj's application-token store, matched to directories::ProjectDirs."""
    data_home = os.environ.get('XDG_DATA_HOME')
    base = Path(data_home) if data_home and Path(data_home).is_absolute() else Path.home() / '.local/share'
    return base / 'forgejo-cli' / 'keys.json'


def merge_cluster_login(path, token):
    """Add the in-cluster host while leaving fj's alias table untouched.

    `fj auth add-token` reassigns the `git.<host>` SSH alias to the newest host,
    which breaks alias-based resolution, so record the extra host in place.
    """
    keys = json.loads(path.read_text()) if path.exists() else {}
    keys.setdefault('hosts', {})[FORGEJO_CLUSTER_HOST] = {'type': 'Application', 'token': token}
    path.write_text(json.dumps(keys, indent=2) + '\n')


def initialize(name, configure):
    secret = Path('/run/cli-tokens') / f'{name}-token'
    if not secret.exists():
        return
    token = secret.read_text().strip()
    if not token:
        raise ValueError(f'{name} token is empty')
    state = Path.home() / '.config/t3-cli-credentials'
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker = state / name
    digest = credential_digest(token)
    if marker.exists() and marker.read_text() == digest:
        return
    configure(token)
    marker.write_text(digest)
    marker.chmod(0o600)
    print(f'Configured persisted {name} CLI login', flush=True)


def forgejo(token):
    run(['fj', 'auth', 'add-token'], input=token + '\n', text=True)
    merge_cluster_login(forgejo_keys_path(), token)
    logins = subprocess.run(['tea', 'login', 'list', '--output', 'json'],
                            check=True, capture_output=True, text=True)
    if any(login.get('name') == 'maio-tech' for login in json.loads(logins.stdout or '[]')):
        run(['tea', 'login', 'delete', 'maio-tech'])
    env = dict(os.environ, GITEA_SERVER_URL=f'https://{FORGEJO_HOST}',
               GITEA_SERVER_TOKEN=token)
    run(['tea', 'login', 'add', '--name', 'maio-tech', '--no-version-check'], env=env)
    run(['tea', 'login', 'default', 'maio-tech'])


def github(token):
    run(['gh', 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https',
         '--insecure-storage', '--with-token'], input=token + '\n', text=True)
    run(['gh', 'auth', 'setup-git', '--hostname', 'github.com'])


if __name__ == '__main__':
    os.umask(0o077)
    run(['git', 'lfs', 'install', '--skip-repo'])
    # Avoid HTTP/2 stream resets on Forgejo's public proxy during pack transfers.
    run(['git', 'config', '--global', 'http.https://forgejo.maio-tech.com/.version',
         'HTTP/1.1'])
    direct = 'http://forgejo-http.forgejo.svc.cluster.local:3000/'
    run(['git', 'config', '--global', f'url.{direct}.insteadOf',
         'https://forgejo.maio-tech.com/'])
    run(['git', 'config', '--global', f'credential.{direct}.helper', 'forgejo'])
    initialize('forgejo', forgejo)
    initialize('github', github)
