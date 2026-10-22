# Intel GPU NFD and device plugin

Flux-managed Node Feature Discovery and Intel GPU support.

## Components

- `cluster/infrastructure/node-feature-discovery`: NFD HelmRelease `0.20.0`
  (OCI `registry.k8s.io/nfd/charts`).
- `cluster/infrastructure/intel-gpu`: Intel GPU plugin HelmRelease `0.37.1`
  (`intel.github.io/helm-charts`).
- GPU plugin uses `sharedDevNum: 1`, `allocationPolicy: none`,
  `nodeFeatureRule: true`, exposing `gpu.intel.com/i915`.

## NFD PCI labels

NFD worker is configured with:

- `sources.pci.deviceClassWhitelist: ["03"]`
- `sources.pci.deviceLabelFields: [class, vendor, device]`

For UHD 630 devices this publishes:

`feature.node.kubernetes.io/pci-0300_8086_3e92.present=true`

The parent Luanti broadcaster should target this exact label.

## Behaviour

- NFD labels Intel GPUs on all four hosts.
- GPU plugin DaemonSet selects `intel.feature.node.kubernetes.io/gpu: "true"`.
- One container per GPU, no sharing.
- i915 is ensured as a kernel module via NixOS on all hosts.
- No host userspace graphics libraries are required; workload images supply
  Mesa/iHD.
- No custom `maio-tech.com/streamer-ready` label is used.

## Verification

- `nix flake check --no-build --no-write-lock-file`
- `nix run nixpkgs#kustomize -- build cluster`
- `nix run nixpkgs#kustomize -- build cluster/infrastructure`
- `git diff --check`
- `helm template` for both pinned charts

## Integration

Parent Luanti broadcaster requires:

- node label `feature.node.kubernetes.io/pci-0300_8086_3e92.present=true`
- extended resource `gpu.intel.com/i915: 1`

Prefer `server4`.

## Limitations

- No deployment, commit, or push performed.
- server4 SSD failure containment remains documented separately.
- Intel GPU plugin chart creates a `GpuDevicePlugin` custom resource; no
  operator HelmRelease is included in this repository.
