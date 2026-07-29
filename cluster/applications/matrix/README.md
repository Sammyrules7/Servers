# Matrix homeserver

This deploys a single stateless Synapse pod at `matrix.maio-tech.com`.
User IDs and room aliases use the delegated server name `maio-tech.com`.
Durable state lives in the `matrix_synapse` PostgreSQL database and the
`matrix-media` Garage bucket.

The Matrix server name is permanent once users or rooms are created.

Synapse uses `synapse-s3-storage-provider` to synchronously store local media,
remote media, and thumbnails in Garage. Local media storage is disabled.
Temporary processing and the provider installation use memory-backed
`emptyDir` volumes, so there is no node-backed media cache or persistent volume.
Remote media objects expire from Garage after 30 days and are fetched again on
demand. URL previews are disabled because Synapse intentionally keeps that
short-lived cache out of external storage providers.

Registration and local password authentication are disabled. Users sign in
exclusively through Authentik. Existing users can be promoted to server
administrators using Synapse's documented database procedure.

## Authentik SSO

Synapse uses the Authentik OIDC issuer
`https://auth.maio-tech.com/application/o/matrix/`. The matching Authentik
provider must be confidential, use an RS256 signing key, and allow:

```text
https://matrix.maio-tech.com/_synapse/client/oidc/callback
```

Configure its back-channel logout URL as:

```text
https://matrix.maio-tech.com/_synapse/client/oidc/backchannel_logout
```

The provider's client ID and secret are stored in the SOPS-encrypted
`oidc-secret.enc.yaml`.

The website at `maio-tech.com` serves Matrix client and federation delegation
from `/.well-known/matrix/client` and `/.well-known/matrix/server`.

Validate discovery and federation after the website and server are deployed:

```sh
curl https://maio-tech.com/.well-known/matrix/client
curl https://maio-tech.com/.well-known/matrix/server
curl https://matrix.maio-tech.com/_matrix/federation/v1/version
```
