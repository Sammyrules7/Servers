# FluxCD GitOps Setup

This directory contains example FluxCD configuration for your K3s cluster.

## Quick Start

Run `flux` locally using nix-shell:

```bash
nix-shell -p fluxcd
```

Or to enter a shell with flux available:

```bash
nix develop
```

## Setup

1. Create a GitHub token with repo access
2. Export it: `export GITHUB_TOKEN=your_token_here`
3. Bootstrap Flux on your K3s cluster:

```bash
flux bootstrap git \
  --url=https://github.com/sammy/Documents-Code-Servers \
  --branch=main \
  --path=clusters/k3s \
  --private=false \
  --password-auth=true
```

The `--password-auth=true` will prompt for your GitHub token.

## Files

- `gitrepository.yaml` - Tells Flux where to find your cluster config
- `kustomization.yaml` - Tells Flux which path to reconcile

## Usage

After bootstrap, add your cluster manifests to `clusters/k3s/` in this repo. Flux will automatically sync them to your K3s cluster.

## Notes

- No permanent changes to your NixOS config - just example YAML files
- The Flux CLI isn't installed via NixOS modules (would run on every boot)
- Use nix-shell for local flux commands instead
- Flux controllers run inside K3s, managed via GitOps