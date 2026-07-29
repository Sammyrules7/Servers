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

Registration is intentionally disabled. Create the first administrator after the
deployment is ready:

```sh
kubectl exec -n matrix deploy/matrix -c synapse -it -- \
  register_new_matrix_user \
  --config /data/homeserver.yaml \
  --user matrix-admin-recovery \
  --admin \
  http://127.0.0.1:8008
```

The command prompts for a password. Keep this local username different from any
Authentik username so Synapse does not need to link two identities implicitly.
Additional local accounts can be created the same way without `--admin`.

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
`oidc-secret.enc.yaml`. Local password authentication remains enabled for an
emergency administrator account.

The website at `maio-tech.com` serves Matrix client and federation delegation
from `/.well-known/matrix/client` and `/.well-known/matrix/server`.

Validate discovery and federation after the website and server are deployed:

```sh
curl https://maio-tech.com/.well-known/matrix/client
curl https://maio-tech.com/.well-known/matrix/server
curl https://matrix.maio-tech.com/_matrix/federation/v1/version
```
