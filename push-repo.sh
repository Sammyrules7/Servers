#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Temporarily remove HelmRelease to test HelmRepository"

# Push to remote
git push origin s3