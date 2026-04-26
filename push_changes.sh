#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Adding changes ==="
git add .

echo "=== Committing changes ==="
git commit -m "Fix Longhorn environment on NixOS: add bind paths for iscsid, enable rpcbind, add required packages"

echo "=== Pushing changes ==="
git push

echo "=== Done ==="