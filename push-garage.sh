#!/bin/bash
set -e

# Add all changes
git add .

# Commit with message
git commit -m "Add Garage Kubernetes operator v0.3.2 and basic GarageCluster configuration

- Install garage-operator Helm chart in garage-operator-system namespace
- Create basic GarageCluster with 3 replicas, 10Gi storage
- Include necessary secrets for RPC and admin access"

# Push to remote
git push origin s3