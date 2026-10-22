# Streamer GPU eligibility

The Luanti broadcaster is stateless and targets hosts exposing the exact Intel
UHD 630 PCI device label:

`feature.node.kubernetes.io/pci-0300_8086_3e92.present=true`

Prefer `server4`. No custom `maio-tech.com/streamer-ready` label is used and no
blanket taint is applied.

`server4` remains subject to the Longhorn write fence and optional cordon
documented in `server4-failing-disk.md`; cordon does not automatically happen
and is an operator decision. Do not drain `server4`.
