# Forgejo shared-store Nix snapshotter builder

This repository owns `.#forgejo-ci-image`, built with the already pinned
`pkgs.nix-snapshotter.buildImage`. It contains Bash, GNU tar (required by the
Kubernetes runner plugin before any workflow step), Git, Nix, Python, curl,
SSH, jq, and basic Unix utilities. No Docker conversion or nested daemon.

The `nix` runner pod mounts the node's `/nix/store` read-only and its
`/nix/var/nix/daemon-socket` read-only. `NIX_REMOTE=daemon` delegates builds to
the **existing host Nix daemon**, which writes the host store and uses the host
substituter/cache configuration. Read-only socket mounts do not prohibit socket
RPC. Jobs do not need write access to the store or root privileges. UID/GID 1774
maps to the dedicated untrusted `forgejo-ci` host account; it is deliberately
not added to Nix `trusted-users`, wheel, or deploy. Kubernetes service-account
tokens are disabled for these job pods. Host daemon socket access must permit
this UID; keep normal sandboxing and do not make this UID trusted.

The local store is shared with builds on the **same node**, not one filesystem
across all cluster nodes. The existing Attic cache provides cross-node reuse
when an authorized operator publishes closures. CI has no Attic push credential.
The host daemon's configured substituters are authoritative for daemon builds;
container Nix settings cannot grant trust or override host policy.

## Bootstrap / rollout order

The currently broken runner cannot build its own replacement: plugin setup
fails before a workflow step executes. Use a working Nix machine/node:

```sh
python3 images/forgejo-ci/update-reference.py
nix build --no-link .#forgejo-ci-tools
image=$(nix eval --raw .#forgejo-ci-image.outPath)
nix eval --raw .#forgejo-ci-image.outPath
attic push main "$image"
```

The runner reference was built on a working Nix machine and is now
`nix:0/nix/store/yiclqp72gdxfmy9q1lfrrz1rdfpm1wlc-nix-image-forgejo-ci.tar`.
The T3 image also built as
`/nix/store/gyfrzn8fzqndfz5p1jhzn393pi1r9k2l-nix-image-t3-code.tar`.
These local builds do not publish closures or deploy the runner. Runs 270 and
271 failed during plugin setup because the legacy image lacked `tar`; no
workflow build step executed. CI cannot verify this replacement until the
operator completes the rollout below. After source changes, rerun the script;
it builds and edits only the image line and never publishes, commits, or deploys.

Review the evaluated reference `nix:0${image}` in
`cluster/applications/forgejo/runners.yaml`. If image source changes, rebuild,
reevaluate, and update that reference; do not invent a store hash.

`lib/kubernetes/k3s.nix` retains the new image via `/etc/forgejo-ci/image` on
all enabled K3s nodes. Deploy those NixOS changes before applying the runner
HelmRelease update through the existing GitOps process. Every eligible node
must resolve the image and its runtime closure through its local store or
Attic with the existing trusted key. Then reconcile/restart the runner through
the normal operator process so the new embedded pod spec is loaded.

Verify a job reaches its first step and reports `command -v tar`, `nix --version`,
and `nix store ping --store daemon`; build T3 and run its regression tests.
Verify a second build reuses the same node store (or published binary cache).
The initial PR does not perform live node, Helm, runner, or cache changes.

Only reviewed/trusted branch code should run with a host daemon socket. This
is build access to a real host, not isolation suitable for arbitrary fork PRs.
Do not enable `pull_request_target`, pass publication credentials to untrusted
code, or broaden daemon trust to work around permissions.
