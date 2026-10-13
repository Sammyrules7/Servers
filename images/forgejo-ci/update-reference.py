#!/usr/bin/env python3
"""Build the snapshotter image and update only the nix runner's reference.

Run from the repository root on a working Nix builder. No deployment/cache push.
"""
import pathlib
import re
import subprocess

subprocess.run(['nix', 'build', '--no-link', '.#forgejo-ci-image'], check=True)
image = subprocess.check_output(
    ['nix', 'eval', '--raw', '.#forgejo-ci-image.outPath'], text=True
).strip()
if not re.fullmatch(r'/nix/store/[a-z0-9]{32}-nix-image-forgejo-ci\.tar', image):
    raise SystemExit(f'Unexpected snapshotter image path: {image!r}')
path = pathlib.Path('cluster/applications/forgejo/runners.yaml')
original = path.read_text()
updated, count = re.subn(
    r'(podspec-nix\.yaml: \|-\n(?:(?!          podspec-).)*?\n              - image: )nix:0/nix/store/[^\s]+',
    lambda m: m[1] + 'nix:0' + image,
    original,
    flags=re.DOTALL,
)
if count != 1:
    raise SystemExit('Expected exactly one nix runner image reference; no file changed')
path.write_text(updated)
print('nix:0' + image)
print('Updated runner reference only. Review diff; publish closure and deploy nodes before runner rollout.')
