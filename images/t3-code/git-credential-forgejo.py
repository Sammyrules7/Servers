"""Serve the mounted Forgejo token only to the in-cluster Git endpoint."""
from pathlib import Path
import sys


if sys.argv[1:] == ['get']:
    fields = dict(line.rstrip('\n').split('=', 1) for line in sys.stdin
                  if '=' in line)
    if (fields.get('protocol') == 'http'
            and fields.get('host') == 'forgejo-http.forgejo.svc.cluster.local:3000'):
        secret = Path('/run/cli-tokens/forgejo-token')
        if secret.exists():
            token = secret.read_text().strip()
            if token:
                print('username=token')
                print(f'password={token}')
