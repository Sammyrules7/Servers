#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

TARGET="${1:-.}"

echo "=== Deploying to $TARGET ==="

if [ "$TARGET" = "." ]; then
  nix run github:zhaofengli/colmena -- apply boot

  echo "=== Touching reboot sentinel for Kured on all nodes ==="
  nix run github:zhaofengli/colmena -- exec -- sudo touch /run/reboot-required
else
  nix run github:zhaofengli/colmena -- apply boot --on "$TARGET"

  echo "=== Touching reboot sentinel for Kured on $TARGET ==="
  nix run github:zhaofengli/colmena -- exec --on "$TARGET" -- sudo touch /run/reboot-required
fi

echo "=== Done ==="
