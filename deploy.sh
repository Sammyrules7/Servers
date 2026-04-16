#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

TARGET="${1:-.}"

echo "=== Deploying to $TARGET ==="
nix run github:serokell/deploy-rs -- "$TARGET"
echo "=== Done ==="