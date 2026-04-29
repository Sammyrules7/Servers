#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Re-add HelmRelease now that HelmRepository is in flux-system"

# Push to remote
git push origin s3