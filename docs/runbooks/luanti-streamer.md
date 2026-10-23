# Luanti broadcaster credentials

The native broadcaster is deployed from the Luanti repository. This repository
owns its SOPS-encrypted Secret at
`cluster/applications/luanti/streamer-secret.enc.yaml`. The `applications` Flux
Kustomization decrypts it with the existing `sops-age-key` identity and creates
`luanti/luanti-streamer`.

From a workstation whose SOPS identity is in `.sops.yaml`:

```sh
sops cluster/applications/luanti/streamer-secret.enc.yaml
```

Keep the existing `stringData.password`: it authenticates the reserved camera
account, and is consumed by both the game server and broadcaster. Rotating it
requires restarting both workloads. It is unrelated to platform stream keys.

Add either or both of these entries under `stringData` in the SOPS editor:

- `youtube-url`: the complete YouTube RTMP(S) ingest URL including its stream key.
- `twitch-url`: the complete Twitch RTMP(S) ingest URL including its stream key.

Use the server URL and key from each platform's creator dashboard. Store the
complete URL, not the key alone. Commit only the encrypted file, push this
repository, and let Flux reconcile `applications`. Never paste keys into chat,
ConfigMaps, Nix expressions, or Git without SOPS encryption.

The initial deployment in Luanti uses `STREAMER_MODE=capture` and records bounded
local clips without publishing. After adding destination credentials, change
`STREAMER_MODE` to `live` in Luanti's `cluster/streamer.yaml` and push that repo.
The resulting rollout reads the destination files. If rotating destination URLs
while already live, restart only the `streamer` Deployment after Flux updates
the Secret; the server does not need a restart if its camera password is unchanged.

The game receives only the camera password via a Secret-backed environment
variable. The broadcaster mounts the Secret at `/run/secrets/streamer` and reads
`password`, `youtube-url`, and `twitch-url` directly. Neither image contains keys.
