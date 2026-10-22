# server4: PM871b endurance FAILED (114%)

Contain new placement without a disk swap or planned downtime. This is not a
complete write block: existing Longhorn replicas, Garage and other local data
continue writing. Backups and healthy replica capacity remain essential.

## Longhorn fence (removed)

The `server4-write-fence` CronJob was removed on 2026-10-22. It had reconciled
every minute, setting the Longhorn node and every discovered disk's
`allowScheduling` to false. It never requested eviction, drained the node, or
deleted replicas.

**Nothing now enforces the fence.** The flag survives only as stored state in the
`server4` `LonghornNode` custom resource. Longhorn does not reset it during normal
operation, but a recreated node object defaults to `allowScheduling: true`, which
would let new replicas land on the failed disk.

Verify the fence is still in place (read-only):

```sh
kubectl -n longhorn-system get nodes.longhorn.io server4 -o yaml
kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io -o custom-columns=NAME:.metadata.name,VOLUME:.spec.volumeName,NODE:.spec.nodeID,STATE:.status.currentState
```

Confirm the node AND every disk report `allowScheduling: false`, no eviction is
requested, and volumes retain healthy replicas. If a flag has flipped back to
true, re-apply it immediately:

```sh
kubectl -n longhorn-system patch nodes.longhorn.io server4 --type=merge -p '{"spec":{"allowScheduling":false}}'
```

Do not compensate by deleting replicas. New/rebuilt replicas need sufficient
healthy disk capacity elsewhere. Best-effort locality cannot override disabled
scheduling.

## Optional operator cordon; never automatic drain

After checking workload placement and healthy-node capacity, an operator may run
`kubectl cordon server4` to stop ordinary new pod placement. Cordon does not stop
existing pods or writes, and DaemonSets/tolerating pods can still run there.
**Do not drain server4** as part of this containment: Garage uses local-path PVCs
and moving/deleting pods can cause an outage. No cordon or drain is automated.

## Garage member-1 replacement (separate maintenance)

The Garage cluster currently has three members, replication factor two,
`layoutPolicy: Auto`, and local-path metadata/data PVCs. A cordon or Longhorn
fence does not migrate Garage data. Do not delete member-1, its PVCs, or server4
until a supported replacement is healthy and data migration is verified.

1. Inventory the GarageCluster, pods, PVC/PV node affinity, Garage version,
   operator version and current layout/status. Map the member-1 pod to its actual
   Garage node ID and server4; do not assume ordinal equals Garage ID. Record
   layout version, zones, capacities, bucket/key configuration and backups.
2. Verify recoverable backups, healthy peers and enough capacity on healthy
   nodes for replication factor two. Check object reads/writes through the
   production endpoint. Stop if replicas are degraded or node identity is unclear.
3. Consult the installed Garage/operator version's replacement procedure. Since
   layout policy is Auto, establish one layout owner before any manual layout
   edits; do not race the operator. Review any temporary replica count, placement
   and layout-policy change separately. This runbook intentionally triggers none.
4. Provision the replacement member on healthy storage using a new identity and
   new PVCs. Preserve the old PVCs. Confirm placement excludes server4 and the
   new member joins the expected cluster/zone with the intended capacity.
5. Following the version-specific procedure, assign replacement capacity and
   remove the old Garage ID in a reviewed layout change. Inspect the proposed
   layout and apply its exact next version only after capacity/quorum checks.
   Do not blindly run `garage layout apply` or remove the old member first.
6. Wait for redistribution and repair to complete. Verify Garage status, layout,
   replication health, errors, and representative object reads/writes; use the
   installed version's documented checks. Keep the old storage until successful
   verification and a recovery window have passed.
7. Only then retire the old member and its PVCs under a separate approved
   maintenance plan. Recheck operator desired state so it cannot recreate the
   retired member on server4. A failed replacement is a stop condition, not a
   reason to delete the remaining good copy.

No migration, layout mutation, PVC deletion or live action is performed by this
repository change. Removing the CronJob later does not re-enable scheduling;
explicitly review node/disk flags and any cordon after healthy storage is ready.
