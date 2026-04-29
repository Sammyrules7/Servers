#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Fix HelmRepository URL and chart name

- url: oci://ghcr.io/rajsinghtech
- chart: charts/garage-operator"

# Push to remote
git push origin s3