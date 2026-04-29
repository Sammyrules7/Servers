#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Temporarily remove HelmRelease to create namespace

- Remove helmrelease.yaml from garage kustomization to allow namespace creation"

# Push to remote
git push origin s3