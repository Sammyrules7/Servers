#!/bin/bash
set -euo pipefail

# Keep projected TLS secrets outside /config: the upstream init recursively
# chowns /config, while Kubernetes secret volumes are read-only.
mkdir -p /config/gamefiles/FactoryGame
ln -sfn /certificates /config/gamefiles/FactoryGame/Certificates
certificate_version=$(readlink -f /certificates/..data)

# A separate process group lets SIGTERM reach the engine and its launcher.
# Background jobs inherit SIGINT as ignored from a non-interactive shell.
setsid /init.sh &
launcher=$!
stop_server() {
  kill -TERM -- "-$launcher" 2>/dev/null || true
}
trap stop_server TERM INT

# Secrets update atomically. Restart gracefully on renewal so the HTTPS API
# loads the new key and certificate together. Kubernetes starts us again.
while kill -0 "$launcher" 2>/dev/null; do
  if [[ $(readlink -f /certificates/..data) != "$certificate_version" ]]; then
    echo 'TLS certificate renewed; stopping server to load the new certificate.'
    stop_server
    break
  fi
  sleep 10 &
  wait $! || true
done
wait "$launcher" || true
# The upstream launcher can exit before its engine finishes saving.
while kill -0 -- "-$launcher" 2>/dev/null; do
  sleep 1 &
  wait $! || true
done
