#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Change Flux GitRepository branch to s3

- Update gotk-sync.yaml to sync from s3 branch instead of main"

# Push to remote
git push origin s3