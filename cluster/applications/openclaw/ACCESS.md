# Sammy cluster read access

This explicit, non-aggregated ClusterRole grants get/list/watch across namespaces only for its enumerated core workload, node, networking and storage resources. Only serviceaccount `openclaw:sammy` is bound; Georgie and Kevin are unchanged. New/custom resource kinds are not automatically included.

Excluded: Secrets (including listing), ConfigMaps, pod logs, all RBAC resources, serviceaccount/token, pod exec/attach/portforward/proxy, node/service proxies, mutation, impersonation, bind and escalate. No wildcard resource, API group, verb, aggregation rule or non-resource URL grants are used. Logs are intentionally excluded because application output can contain credentials. ConfigMaps and arbitrary custom resources are also excluded because their payloads may carry secrets.

Kubernetes RBAC cannot redact fields: granted objects may contain inline environment credentials, annotations, commands, event messages or storage parameters. Keep credentials out of those objects. This role prevents access to Secret resources, not every possible occurrence of sensitive data. Existing grants are additive and must be audited separately, including the operator's existing self-config permission and any other bindings. RBAC cannot revoke an existing grant. Other credentials already mounted in the agent remain usable; this change does not remove them.

After review/merge and GitOps reconciliation, a cluster administrator should verify effective permissions (do not print secret contents):

```sh
kubectl auth can-i list pods --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i get nodes --as=system:serviceaccount:openclaw:sammy
# Each of the following must answer no; investigate existing bindings otherwise.
kubectl auth can-i get secrets --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i list secrets --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i get configmaps --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i get pods/log --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i create pods/exec --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i create serviceaccounts/token --all-namespaces --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i list clusterroles --as=system:serviceaccount:openclaw:sammy
kubectl auth can-i patch deployments --all-namespaces --as=system:serviceaccount:openclaw:sammy
```

This PR changes no gateway/node execution configuration. Desktop/laptop node approval policy is maintained in the separate workstation repository. Android commands remain limited to implemented/advertised capabilities and Android permission/consent gates; no shell, camera or screen capability is manufactured by an allowlist change.
