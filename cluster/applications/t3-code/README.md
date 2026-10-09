T3 Code is served at https://t3.maio-tech.com through the existing HTTPS gateway
and Cloudflare DNS/proxy. T3's remote pairing authentication protects the server;
no anonymous agent access is enabled. Pair using `t3 pair` inside the pod and
replace the printed local address with `https://t3.maio-tech.com`, preserving the
pairing path and token. Pairing URLs are credentials.

The environment advertises the friendly name `Kubernetes` from the mounted
`/etc/machine-info`; its container hostname is the stable `kubernetes`.

The Nix image resolves `t3@nightly` and `@openai/codex@latest` at startup and checks
npm hourly. It verifies both executables before atomically selecting a new
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

The image uses the host's read-only `/nix/store` and Nix daemon socket. Builds and
substitutions therefore share the host cache, including Attic. A dedicated UID
1773 maps to the untrusted `t3-code` host account; the pod has no Kubernetes token.
Nix builds run in the host daemon's sandbox. The daemon connection intentionally
lets approved coding sessions request host builds.

In the T3 terminal, clone projects under `/workspace`, run `direnv allow` for
reviewed `.envrc` files, and use `use flake` or `nix develop`. Bash loads direnv;
the Codex wrapper also loads the approved environment for noninteractive provider
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
