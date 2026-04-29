#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Add passCredentials to HelmRepository"

# Push to remote
git push origin s3