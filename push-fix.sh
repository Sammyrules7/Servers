#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Fix HelmRepository URL for OCI

- Change URL to registry path without chart name"

# Push to remote
git push origin s3