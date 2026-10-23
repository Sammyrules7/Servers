# Luanti broadcaster

The application deployment, SOPS-encrypted credentials and operating instructions
live together in the [Luanti repository](https://forgejo.maio-tech.com/Sammy/Luanti/src/branch/main/streamer/README.md).

Edit `cluster/streamer-secret.enc.yaml` from the Luanti checkout using its local
`.sops.yaml` policy. Flux creates `luanti/luanti-streamer`; the broadcaster mounts
its credential files. Preserve `password` when adding `youtube-url` or `twitch-url`.

This repository owns NFD/Intel GPU infrastructure, the Luanti Flux entrypoint,
and the shared `flux-system/sops-age-key` identity. The Luanti Kustomization's
`spec.decryption` enables application-owned encrypted secrets.
