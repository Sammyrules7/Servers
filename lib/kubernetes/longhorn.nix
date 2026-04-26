{ config, lib, ... }:

{
  # Longhorn modules
  services.envfs.enable = true;
  boot.kernelModules = [
    "dm_snapshot"
    "dm_mirror"
    "dm_thin_pool"
    "iscsi_tcp"
  ];

  services.openiscsi = {
    enable = true;
    name = "iqn.2016-04.com.open-iscsi:${config.networking.hostName}";
  };

  # Workaround for Longhorn on NixOS: symlink /usr/local/bin to Nix bin
  systemd.tmpfiles.rules = [
    "L+ /usr/local/bin - - - - /run/current-system/sw/bin/"
  ];

  # Enable NFS client for Longhorn RWX volumes
  services.rpcbind.enable = true;

  environment.systemPackages = with config.pkgs; [
    bash
    nfs-utils
    jq
    openiscsi
  ];
}