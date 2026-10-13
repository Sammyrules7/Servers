T3 Code is served at https://t3.maio-tech.com through the existing HTTPS gateway
and Cloudflare DNS/proxy. T3's remote pairing authentication protects the server;
no anonymous agent access is enabled. Pair using `t3 pair` inside the pod and
replace the printed local address with `https://t3.maio-tech.com`, preserving the
pairing path and token. Pairing URLs are credentials.

The environment advertises the friendly name `Kubernetes` from the mounted
`/etc/machine-info`; its container hostname is the stable `kubernetes`.

The Nix image resolves `t3@nightly`, `@openai/codex@latest`, and `opencode-ai@dev` at startup and checks
npm hourly. It verifies all three executables before atomically selecting a new
installation and restarting T3. Updates can interrupt active sessions. Failed
updates keep the installed release; first boot requires npm access. Runtime
versions, npm's download cache, credentials, and projects persist on Longhorn.
Use `cat /data/runtime/current/versions.json` in the pod to inspect versions.

Codex's login and configuration are persisted at `/data/home/.codex` (explicit
`CODEX_HOME`). T3 settings, conversations, pairing grants, and provider state
are persisted at `/data/t3` (`T3CODE_HOME`). Both survive updates, pod restarts,
and rescheduling because they are on the same Longhorn PVC. Do not delete the
PVC when replacing the deployment. Sign in once from the container terminal
with `codex login --device-auth`; subsequent Codex updates reuse that login.

`fj`, `tea`, and `gh` are installed in the Nix image. `fj` defaults to
`forgejo.maio-tech.com` (override with `-H`); `tea` defaults to the `maio-tech`
login. Both use the supplied Forgejo token. `gh` uses the existing GitHub login
and configures HTTPS Git authentication. The tokens are stored in the SOPS
encrypted `cli-tokens.enc.yaml` and mounted read-only; startup initializes the
CLI configurations under the persisted `/data/home/.config`. Token changes
are picked up at the next pod restart. No token is embedded in the image.

Git LFS is installed and its global filters are initialized at startup. HTTPS
Git transfers to `forgejo.maio-tech.com` use HTTP/1.1 to avoid HTTP/2 stream
resets through the public proxy; other hosts keep Git's default protocol.
Inside this container, Git rewrites `https://forgejo.maio-tech.com/` to the
in-cluster Forgejo HTTP service, keeping the public URL saved as the remote.
Git LFS uses the same direct endpoint. A host-scoped credential helper reads the
mounted Forgejo token when needed, without copying it into Git configuration.

The image uses the host's read-only `/nix/store` and Nix daemon socket. Builds and
substitutions therefore share the host cache, including Attic. A dedicated UID
1773 maps to the untrusted `t3-code` host account; the pod has no Kubernetes token.
Nix builds run in the host daemon's sandbox. The daemon connection intentionally
lets approved coding sessions request host builds.

In the T3 terminal, clone projects under `/workspace`, run `direnv allow` for
reviewed `.envrc` files, and use `use flake` or `nix develop`. Bash loads direnv;
the Codex and OpenCode wrappers also load the approved environment for noninteractive provider
processes. nix-direnv puts cached profiles in a writable host GC-root directory
so host garbage collection preserves them. These profiles are cached per node;
Longhorn retains the workspace and npm cache if the pod moves between nodes.
Remove unused project directories from `/nix/var/nix/gcroots/t3-code` on their
node when their cached development dependencies should become collectible.

To change the base image:

```sh
nix build .#t3-code-image
attic push main "$(nix eval --raw .#t3-code-image.outPath)"
nix run .#colmena -- apply switch
```

Update `deployment.yaml` to `nix:0` plus the evaluated image store path before
committing. All cluster nodes retain the image via `/etc/t3-code/image`; deploy
the NixOS changes before Flux starts a pod using a new image. npm releases update
automatically and do not require rebuilding the image or editing manifests.

OpenCode is available as `opencode` in the container terminal, with approved
project direnv environments loaded by its wrapper. This adds a standalone CLI,
not native OpenCode provider integration in T3. The `dev` channel (not `tui-v2`)
is unstable: hourly updates may introduce incompatible behavior and restart T3
even when only OpenCode changes. All three binaries must pass `--version`
before the release is activated; failures retain the previous release.

OpenCode uses its default XDG locations under the existing PVC-backed
`HOME=/data/home`: configuration at `/data/home/.config/opencode` and data,
authentication, and sessions at `/data/home/.local/share/opencode`. Cache and
state under HOME persist too. No OpenCode credentials are provisioned by the
image; authenticate interactively as needed. Explicit XDG overrides can change
these locations and should also point into persistent storage.

npm lifecycle scripts remain disabled with `--ignore-scripts`. The inspected
OpenCode dev tarball declares `bin/opencode.exe`, which its postinstall normally
populates from a platform optional dependency. For this x86_64/glibc image the
installer explicitly installs the matching-version
`opencode-linux-x64-baseline` package, copies its native binary to that target,
and creates the CLI link without executing upstream postinstall or other
lifecycle scripts. The baseline variant avoids an AVX2 requirement. Package
layout changes fail closed during staging; a future architecture change must
update this platform selection and the image's ELF loader together.

### Build-only CI for the OpenCode PR

`.forgejo/workflows/t3-code.yaml` reuses the existing Forgejo `nix` label and
its Kubernetes builder pod, read-only host store, and mounted host daemon
socket. It deliberately avoids installing another CI platform, Docker-in-Docker,
and Node-based checkout/upload actions. The repository-owned `forgejo-ci-image`
provides a shell, Git, GNU tar, and Nix; its untrusted UID must be allowed to
connect to the host daemon. See `images/forgejo-ci/README.md` for the bootstrap
and shared-cache rollout order. Configuration alone cannot prove live readiness.

Only pushes to `main`, `feat/t3-opencode-dev`, or `feat/nix-snapshotter-ci`,
or manual dispatch on one of those same branches, run this workflow. Arbitrary pull requests/forks are not run on the host-daemon
builder. Checkout uses the automatic job token without persisting it; no Actions
secrets or Kubernetes credentials are requested. This is a branch-scoped PR
build, not a general untrusted-PR pipeline.

CI builds `.#forgejo-ci-image`, `.#t3-code-tools`, and `.#t3-code-image`, runs all Python regression
tests using the built tools, then evaluates the image path. It writes
`ci-output/image-store-path.txt`, `ci-output/image-reference.txt`, and
`ci-output/deployment.patch` in the ephemeral job workspace and prints their
contents in the final step's log. These are **log outputs, not uploaded artifacts**;
copy the patch from the log for review. No generated commit or deployment is
performed. The build does not validate running the complete container or npm
nightly binaries inside the final image.

After a successful run, an operator still needs to publish the image closure to
Attic using existing authorized credentials, review/apply the deployment patch,
and deploy the NixOS changes so every eligible node retains the image before
Flux rolls out the new pod. CI has no cache-push credential and does not perform
those steps. A queued run requires an online runner with the `nix` label; a
missing-tool/socket or daemon-permission failure requires fixing the existing
builder environment, not adding repository secrets.
