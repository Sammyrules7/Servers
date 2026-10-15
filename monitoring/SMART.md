# SMART disk alerts

NixOS runs smartd with local wall notifications and temperature warnings at 55/65 C.
VictoriaMetrics scrapes smartctl exporters on each node's Tailscale address, port
9633, and evaluates the SMART VMRule through the existing alerting stack. Check
Alertmanager receivers before relying on remote delivery; no new receiver or
credentials are configured here. Apply the NixOS configuration before expecting
the exporters to be up.

On SmartDiskFailed, identify the physical disk using `smartctl -x /dev/DEVICE`
and match its serial/mount path to the Longhorn node disk. **Immediately disable
Allow Scheduling on that disk in Longhorn**, even when its Ready condition is
true: Ready does not certify SMART health. Verify healthy replicas and available
capacity, then evacuate replicas and replace the disk. Do not delete replicas or
remove the disk until healthy copies exist elsewhere.

Endurance warns at 90% consumed (NVMe/SCSI); ATA wear alerts compare normalized
wear attributes against 10% remaining or the vendor threshold. ATA names vary by firmware: inspect
exported attributes when commissioning a disk. Media errors include NVMe errors
and ATA reallocated/pending/uncorrectable sectors. Temperature warns at 65 C for
10 minutes. Reset growth means unexpected power-loss attribute growth or more
than three power cycles in an hour; these gauges use delta to avoid treating a
counter reset as growth. Correlate with maintenance and kernel/controller logs.
