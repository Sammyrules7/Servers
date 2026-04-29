#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Remove global namespace from garage kustomization

- Allow resources to use their own namespaces"

# Push to remote
git push origin s3