# Satisfactory

Connect using **Server Manager → Add Server**, address
`satisfactory.maio-tech.com`, port `7777`. The server is named `Maio Factory`.
Use the administrator password to manage it and create or upload your world.
Share only the player password with friends. Retrieve them locally:

```sh
kubectl -n satisfactory get secret satisfactory-passwords -o jsonpath='{.data.admin-password}' | base64 -d; echo
kubectl -n satisfactory get secret satisfactory-passwords -o jsonpath='{.data.player-password}' | base64 -d; echo
```

Passwords are SOPS encrypted in Git. The bootstrap Job claims a fresh server,
sets both passwords, and enables `FG.DSAutoPause` and
`FG.DSAutoSaveOnDisconnect`. It leaves world creation and starting location to
the administrator. To rerun bootstrap with the stored credentials, delete its
Job and reconcile the `satisfactory` Flux Kustomization. Changing the Secret
alone does not change the passwords stored by the game; change passwords
through Server Manager and update the encrypted Secret to match.

## DNS and network

Cloudflare has a DNS-only A record for `satisfactory.maio-tech.com` pointing
to `70.73.101.233`. Keep it DNS-only; the normal Cloudflare HTTP proxy cannot
carry this game's UDP and messaging connections. Update the record if the
public IP changes. No AAAA record is configured.

OPNsense forwards these ports to **192.168.1.13 (server3)**, preserving the
same external and internal port numbers, with associated WAN allow rules:

| Port | Protocol | Purpose |
| --- | --- | --- |
| 7777 | TCP | HTTPS server management API |
| 7777 | UDP | Game traffic and server discovery |
| 8888 | TCP | Reliable messaging |

The forwards enable NAT reflection for access through the public hostname
from the LAN. Router administration from the laptop can use an SSH tunnel:
`ssh -N -L 8443:192.168.1.1:443 server3`, then `https://localhost:8443`.
Router credentials stay outside Git. All four servers advertise Tailscale
exit-node capability through `lib/tailscale.nix`, with IPv4/IPv6 forwarding
managed by NixOS. All four were approved in the tailnet admin console. Select a home server
as the laptop's exit node when accessing the home network.

K3s ServiceLB exposes these ports on the home cluster nodes and routes them
to the game pod. Friends can alternatively use Tailscale and add
`100.119.85.83:7777`; the certificate is issued for the DNS name, so using
the IP can produce a hostname warning. For LAN access using the public
hostname, configure NAT reflection or split DNS pointing the hostname to
`192.168.1.13`. DNS-01 certificate issuance does not require inbound port 80.

## Certificates, storage, and resources

The app lives in its own `satisfactory` namespace and uses the shared Let’s
Encrypt ClusterIssuer. Its SOPS-encrypted Cloudflare DNS token lives in
`cert-manager`, alongside the ACME account key. Cert-manager renews
`satisfactory-tls` automatically. The projected
Secret supplies the engine's `cert_chain.pem` and `private_key.pem` files.
The launcher gracefully restarts the game on certificate replacement;
renewal briefly disconnects players. No certificate or private key is in Git.

The server uses a 30 GiB Longhorn PVC, `satisfactory-data-longhorn`, for
`/config`, with the cluster storage class's replicated storage settings.
It can schedule on home nodes and reattach its volume on a different node.
Longhorn's CSI services were recovered after server2 returned, and the
initial downloaded files were migrated onto Longhorn before completing
this deployment. No local-path volume is used by the final workload.

The game supports four players, requests one CPU and 4 GiB RAM, and is
limited to four CPUs and 8 GiB RAM. Large factories may need more RAM.
Ten rotating autosaves and the image's startup backup stay on the same
volume: download saves regularly through Server Manager and keep copies
outside the cluster. Saves are under `/config/saved/server`; game files and
configuration also persist across pod restarts. The stable game version
updates on container startup, so clients should use the matching stable
release. The container image is pinned separately to `v1.9.10`.

Auto-pause stops simulation while empty, reducing CPU use while retaining
RAM and allowing players to reconnect normally. Full scale-to-zero would
need a separate wake mechanism for UDP/TCP clients. If you need to free RAM
manually, set `spec.replicas: 0` in the deployment and commit it; set it back
to `1` to resume. Direct `kubectl scale` is reverted by Flux.

No documented cracked-client/ownership-check toggle exists in the standard
container. This deployment uses the unmodified dedicated server; cracked
client compatibility is unverified. `-NoSteamClient` is not a license-check
bypass. Server and client game versions must match.

## Operations

```sh
flux reconcile kustomization satisfactory --with-source
kubectl -n satisfactory get deployment satisfactory
kubectl -n satisfactory logs deployment/satisfactory --tail=100
kubectl -n satisfactory logs job/satisfactory-bootstrap
kubectl -n satisfactory get certificate satisfactory
```

The separate Flux Kustomization depends only on infrastructure, so unrelated
main-instance/application dependency failures do not block this deployment.
Deleting the PVC deletes its volume and data: retain it when changing the workload.

References: [container documentation](https://github.com/wolveix/satisfactory-server),
[dedicated server API and certificate paths](https://github.com/wolveix/satisfactory-server/wiki/Official-API-Docs).

Deployment verification passed: administrator/player authentication,
auto-pause and disconnect-save settings, public HTTPS with normal trust
validation, public TCP 8888, and a public UDP 7777 query. The Longhorn volume
was healthy with two replicas, and all four Tailscale peers were online and
available as exit nodes. In-game joining still needs a client and a world.
