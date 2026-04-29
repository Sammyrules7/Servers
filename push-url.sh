#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Revert HelmRepository URL to full path

- Change back to oci://ghcr.io/rajsinghtech/charts/garage-operator"

# Push to remote
git push origin s3