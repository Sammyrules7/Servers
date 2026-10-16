"""Initialize persisted CLI logins from projected secrets without logging tokens."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

FORGEJO_HOST = 'forgejo.maio-tech.com'
GITHUB_HOST = 'github.com'
TOKEN_DIRECTORY = Path('/run/cli-tokens')
# Bump when the configuration commands change so already-provisioned pods
# reconfigure once instead of trusting a stale marker.
CONFIG_REVISION = 3
# Earlier revisions rewrote Git to the in-cluster service so transfers stayed off
# the public proxy. `git remote get-url` reports the rewritten URL, and T3 derives
# a repository's change-request host from it, so the rewrite made T3 look for a
# host that no pull request link uses. The pod now answers the public name itself
# (forward-forgejo.py); these keys are removed from homes that already carry them.
LEGACY_CLUSTER_HOST = 'forgejo-http.forgejo.svc.cluster.local:3000'
STALE_GIT_KEYS = (
    f'url.http://{LEGACY_CLUSTER_HOST}/.insteadOf',
    f'credential.http://{LEGACY_CLUSTER_HOST}/.helper',
    f'http.https://{FORGEJO_HOST}/.version',
)
# Git asks a URL-scoped helper for a password only for that host. The helper baked
# into the image answers for the retired in-cluster endpoint, so declare the
# equivalent here rather than requiring an image rebuild.
FORGEJO_HELPER = ('!f() { echo username=token; echo "password=$(cat '
                  + str(TOKEN_DIRECTORY / 'forgejo-token') + ')"; }; f')


def run(command, **kwargs):
    return subprocess.run(command, check=True, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, **kwargs)


def credential_digest(token):
    return hashlib.sha256(f'{CONFIG_REVISION}\0{token}'.encode()).hexdigest()


def configure_git():
    run(['git', 'lfs', 'install', '--skip-repo'])
    for key in STALE_GIT_KEYS:
        subprocess.run(['git', 'config', '--global', '--unset-all', key],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run(['git', 'config', '--global', f'credential.https://{FORGEJO_HOST}.helper',
         FORGEJO_HELPER])


def initialize(name, configure, attempts=6, delay=5):
    """Provision a login once per credential, tolerating a briefly unavailable server.

    `forgejo.maio-tech.com` is answered by this pod's own forwarder, which may
    still be starting, and either server can refuse for a moment. A failed attempt
    leaves the marker absent, so the next start retries instead of holding the pod
    in a crash loop while Git and T3 are otherwise usable.
    """
    secret = TOKEN_DIRECTORY / f'{name}-token'
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
    for attempt in range(1, attempts + 1):
        try:
            configure(token)
        except (subprocess.CalledProcessError, OSError) as error:
            print(f'Could not configure the {name} CLI (attempt {attempt}/{attempts}): {error}',
                  flush=True)
            time.sleep(delay)
            continue
        marker.write_text(digest)
        marker.chmod(0o600)
        print(f'Configured persisted {name} CLI login', flush=True)
        return
    print(f'The {name} CLI login is not configured; the next start retries', flush=True)


def forgejo(token):
    run(['fj', 'auth', 'add-token'], input=token + '\n', text=True)
    logins = subprocess.run(['tea', 'login', 'list', '--output', 'json'],
                            check=True, capture_output=True, text=True)
    if any(login.get('name') == 'maio-tech' for login in json.loads(logins.stdout or '[]')):
        run(['tea', 'login', 'delete', 'maio-tech'])
    env = dict(os.environ, GITEA_SERVER_URL=f'https://{FORGEJO_HOST}',
               GITEA_SERVER_TOKEN=token)
    run(['tea', 'login', 'add', '--name', 'maio-tech', '--no-version-check'], env=env)
    run(['tea', 'login', 'default', 'maio-tech'])


def github(token):
    run(['gh', 'auth', 'login', '--hostname', GITHUB_HOST, '--git-protocol', 'https',
         '--insecure-storage', '--with-token'], input=token + '\n', text=True)
    run(['gh', 'auth', 'setup-git', '--hostname', GITHUB_HOST])


if __name__ == '__main__':
    os.umask(0o077)
    configure_git()
    initialize('forgejo', forgejo)
    initialize('github', github)
