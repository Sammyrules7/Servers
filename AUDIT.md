# Cluster and NixOS audit — 2026-09-06

Reviewed the Kubernetes configuration, flake, shared modules, host hardware
configuration, and deployment script. Inspected all four servers over SSH.
The initial audit used read-only live inspection. The user subsequently
authorized live deployment and testing; results are recorded below.

## Fixes prepared

| Finding | Change |
| --- | --- |
| Cloudflare mTLS targeted nonexistent Gateway `envoy`. The live policy had no attachment status. | Target `gateway`, restricted to `websecure-tld` and `websecure-sub`. Direct Attic and S3 listeners remain outside the policy. |
| Runner internet egress excluded only pod and Service CIDRs, allowing private LAN, Tailscale, and link-local destinations. | Exclude those networks while retaining explicit DNS, Forgejo, and runner-cache access. Disable automatic service-account token mounting in job pod templates; the runner manager retains its token. |
| PgBouncer `internalTrafficPolicy: Local` makes clients depend on their own node's pooler being ready. | Use `Cluster` so another healthy pooler can serve them during replacement or failure. |
| Attic API, migrations, and daily GC independently used mutable `latest`. | Pin all three to the same digest verified in the running API, completed migration, and recent GC jobs. |
| Attic secret bootstrap could continue after key generation failed. | Enable Bash error and pipeline failure handling. Existing immutable jobs remain protected by Flux's `IfNotPresent` annotation. |
| Tailscale firewall rule opened UDP 4163, while every inspected daemon listened on 41641. | Derive the rule from `services.tailscale.port`. |
| server2's intended lz4/75% zram override lost to shared settings. Live server2 used zstd/150%. | Make shared settings defaults and the host override explicit. |
| The deployment user configuration supplied an empty default password. | Configure a locked initial password hash, retaining SSH keys and passwordless deployment sudo. With `mutableUsers = true`, existing account hashes are preserved. |
| GC unit specified invalid I/O class `best-effect`. | Correct to `best-effort`. |
| Flake checks did not evaluate the host systems. | Add all four host derivations to `checks`; remove unused `nixpkgs-stable` input and its lock entry without updating other inputs. |

Listener-specific policy attachment is documented by
[Envoy Gateway](https://gateway.envoyproxy.io/latest/concepts/gateway_api_extensions/client-traffic-policy/).
The pooler failure mode follows Kubernetes' documented
[internal traffic policy behavior](https://kubernetes.io/docs/concepts/services-networking/service-traffic-policy/).

## Remaining findings

- **High: recovery coverage is missing.** No CNPG `Backup` or `ScheduledBackup`
  resources were found. Longhorn's default backup target has no URL or credential
  and is unavailable; no recurring jobs were found. PostgreSQL and Garage use
  local-path storage. Replicas provide redundancy but do not establish a tested
  recovery path for deletion or a site loss. Choose an independent backup
  destination, credentials, and retention policy, then test restoration. Local
  etcd snapshots exist on server1; their presence does not establish off-site
  backup coverage or application-data recovery. External backup systems were not
  verified.
- **Medium: one control-plane failure domain.** All three etcd/control-plane
  nodes are labeled `home`; server2 at `alt` is an agent. Losing the home site
  therefore loses control-plane quorum. Site resilience requires a topology
  decision beyond adding another replica.
- **Medium: Flux bootstrap ownership drift.** Normal root server-side dry run
  conflicts with manager `flux` on the Flux pod quota and controller CPU limits
  and `GOMEMLIMIT` fields. Live Flux reconciliation is Ready. A forced dry run
  passes, but that does not resolve ownership. Review bootstrap versus GitOps
  ownership before regenerating or reinstalling Flux; no live ownership was
  taken over during this audit.
- **Medium: remaining mutable dependencies.** Prometheus CRDs come from `main`,
  and Cloudflare origin issuer resources come from `trunk`. Some bootstrap and
  tooling images remain mutable, and Matrix installs Python dependencies during
  pod startup. Pin upstream resources and bake runtime dependencies into images
  to make rebuilds independent of upstream branch and package changes.
- **Capacity observation:** server4 reported about 420 MiB available memory in
  one sample, although no node pressure conditions or recorded container
  `OOMKilled` last states were present. Review memory trends before increasing
  workload capacity. Disk usage on servers2–4 was 48–58%.

## Validation and deployment limits

- All four nodes Ready; no failed systemd units on any server. All four Flux
  Kustomizations and 12 HelmReleases Ready. Across 120 pods, none was unhealthy
  by phase/container readiness; completed jobs were excluded from that check.
- PostgreSQL reported two ready instances; all five Longhorn volumes were
  healthy. All four ingress certificates were Ready. No current warning events
  were returned.
- `nix flake check --no-build --no-write-lock-file` passed with all four host
  derivations evaluated. Explicit option evaluation confirmed server2 lz4/75%,
  the other hosts zstd/150%, UDP 41641, locked deployment passwords, and corrected
  GC I/O class. Full system builds and activation were not performed.
- All repository YAML documents parsed with duplicate-key checking; embedded
  dashboard JSON and YAML configuration parsed. The only unencrypted Kubernetes
  Secret found contains the public Cloudflare CA certificate.
- Kustomize rendered root (37 resources), infrastructure (82), main-instances
  (11), and applications (87). Server-side dry runs passed for all non-Secret
  resources, with the root ownership exception described above. Encrypted
  Secrets and the immutable `IfNotPresent` bootstrap Job were excluded from
  those apply dry runs. Secrets were not decrypted.
- `git diff --check` passed. API dry runs validate admission, not controller
  behavior or end-to-end service operation.

After rollout, verify the mTLS policy is Accepted for both intended listeners,
Cloudflare requests succeed, and direct Attic/S3 clients still work. The
Cloudflare-facing routes must have Authenticated Origin Pulls configured before
enforcement. Exercise a Forgejo job to confirm its labels match the policy,
required public access works, and private access is denied. NetworkPolicy alone
is not a complete sandbox for untrusted jobs. The swap change should be applied
through the existing boot-and-Kured deployment flow rather than resizing live
swap on a loaded node. Verify SSH and sudo after the NixOS rollout.
