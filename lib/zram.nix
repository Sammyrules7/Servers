{
  config,
  pkgs,
  lib,
  ...
}:

{
  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 150;
  };

  boot.kernel.sysctl = {
    "vm.swappiness" = 100;
    "vm.min_free_kbytes" = 524288;
    "vm.watermark_scale_factor" = 2000;
  };

  services.k3s = {
    extraFlags = [
      "--kubelet-arg=fail-swap-on=false"
    ];
    extraKubeletConfig = {
      failSwapOn = false;
      memorySwap = {
        swapBehavior = "LimitedSwap";
      };
    };
  };
}
