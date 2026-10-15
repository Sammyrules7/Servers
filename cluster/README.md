# Flux health and alerts

`infrastructure`, `main-instances`, and `applications` wait for the health of all
resources they apply (including HelmReleases and nested Flux Kustomizations).
Their timeouts are 15m, 10m, and 15m respectively. Existing dependency ordering
therefore gates applications on healthy infrastructure and main instances.
A failed `luanti` or `vr-platform` Kustomization makes `applications` fail its
health check instead of reporting success merely because the manifests applied.

The root `flux-system` checks these three boundaries plus `satisfactory`
explicitly. Its 60m timeout allows for dependency sequencing and the existing
30m satisfactory timeout. It does not check itself. The root settings are patched
in `cluster/kustomization.yaml`; generated `flux-system/gotk-sync.yaml` stays
bootstrap-owned. Standalone bootstrap initially uses the generated settings;
the first reconciliation of `./cluster` applies the root health-check patch.

Health is sampled during reconciliation, not continuously: failures become
visible on the next reconciliation and may take the health timeout to settle as
`Ready=False` (`HealthCheckFailed`). Inspect the child conditions for the cause:

```sh
flux get kustomizations -A
kubectl -n flux-system describe kustomization applications
kubectl -n flux-system describe kustomization flux-system
```

For notifications, reuse an existing Flux notification-controller Provider and
an Alert with `eventSeverity: error` and `eventSources` selecting
`kind: Kustomization`, `name: '*'`, `namespace: flux-system`. This catches direct
child errors as well as parent health failures. Configure a real receiver before
adding an Alert; no new receiver or credentials are installed here. If controller
metrics are already scraped, alert on `gotk_reconcile_condition{type="Ready",
status="False",kind="Kustomization"} == 1` for 5m and handle missing metrics
separately. Verify the metric labels against the deployed Flux version.
