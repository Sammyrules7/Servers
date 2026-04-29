#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Re-add HelmRelease now that namespace exists

- Add helmrelease.yaml back to garage kustomization"

# Push to remote
git push origin s3