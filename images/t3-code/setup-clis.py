"""Initialize persisted CLI logins from projected secrets without logging tokens."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def run(command, **kwargs):
    return subprocess.run(command, check=True, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, **kwargs)


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
    digest = hashlib.sha256(token.encode()).hexdigest()
    if marker.exists() and marker.read_text() == digest:
        return
    configure(token)
    marker.write_text(digest)
    marker.chmod(0o600)
    print(f'Configured persisted {name} CLI login', flush=True)


def forgejo(token):
    run(['fj', 'auth', 'add-token'], input=token + '\n', text=True)
    logins = subprocess.run(['tea', 'login', 'list', '--output', 'json'],
                            check=True, capture_output=True, text=True)
    if any(login.get('name') == 'maio-tech' for login in json.loads(logins.stdout or '[]')):
        run(['tea', 'login', 'delete', 'maio-tech'])
    env = dict(os.environ, GITEA_SERVER_URL='https://forgejo.maio-tech.com',
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
