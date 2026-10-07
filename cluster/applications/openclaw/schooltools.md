# Managed schooltools (Sammy only)

`schooltools-patch.yaml` adds one non-root init container to Sammy's existing
OpenClawInstance. It builds `IamCoder18/schooltools` at an exact Git commit using
the existing Go image and installs the binary in the existing PVC-backed
`/data/.local/bin` (runtime `/home/openclaw/.local/bin`, already on PATH).
No CBE credentials, login, permissions, RBAC, prompts or OpenClaw policy changes
are part of this installation. Other instances are unchanged.

## Distribution choice

At introduction, upstream had no Git tags/releases to install. Its `go.mod`
declares `github.com/aarav/schooltools`, not its GitHub repository path, so a
remote `go install github.com/IamCoder18/schooltools@...` is not appropriate.
Build the checked-out, commit-pinned module instead; dependencies are verified
against upstream `go.sum`. `GOTOOLCHAIN=local` prevents implicit Go downloads.
The installer verifies the fetched commit, runs dependency verification and
unit tests, builds with `-mod=readonly`, and smoke-tests `--version`. Replacement
of the existing binary is atomic and the commit marker is written only after
success. An unchanged pin and existing binary skip reinstall on later starts.

## Automatic upgrades

The existing daily Renovate CronJob handles updates. A narrowly scoped regex
manager in root `renovate.json` watches upstream `main` through the supported
`git-refs` datasource and rewrites **only the full commit pin**. Only this
schooltools digest dependency is configured for Renovate-managed PR automerge
(`platformAutomerge: false`), subject to existing repository checks, merge
permissions and branch protections. No checks/protections are bypassed or
changed. It does not fetch and execute an unpinned branch during pod startup.

After the initial PR is merged, Flux must reconcile the repository and the
operator must roll out the changed instance; nothing is installed in the live
cluster by opening the PR. The committed Flux bootstrap source still names
`ssh://git@github.com/sammyrules7/servers`, whereas this PR targets Forgejo
`Sammy/Servers`. Confirm that the live Flux source tracks Forgejo or that an
existing synchronization path carries these commits to the tracked repository.
This change deliberately does not alter Flux bootstrap ownership or credentials.
Future merged pin changes follow the same path.
A failed fetch, dependency verification, test or build fails the init container
and prevents the updated pod starting rather than silently accepting a broken
upgrade. A future upstream Go-version requirement may require an explicit Go
image update. The old PVC binary is retained on pre-install failure, but that
does not bypass the failed init container.

Daily timing depends on the existing Renovate job and Flux reconciliation;
server-side merge restrictions may leave update PRs waiting for review. For a
rollback, disable this dependency's automerge/update rule and revert the pin in
Git, then let normal Flux/operator reconciliation apply it. There is no new
CronJob or live self-updater.
