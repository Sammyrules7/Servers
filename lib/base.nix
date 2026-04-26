{ pkgs, self, config, lib, ... }:
{
   imports = [
     ./deployment.nix
     ./user-auth.nix
     ./net-conf.nix
     ./boot-conf.nix
     ./ssh.nix
     ./sys-conf.nix
     ./nix-gc.nix
     ./nix.nix
     ./tailscale.nix
     ./k3s.nix
    ];

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

    # Workaround for Longhorn on NixOS: bind Nix paths to /bin for nsenter
    systemd.services.iscsid.serviceConfig = {
      PrivateMounts = "yes";
      BindPaths = "/run/current-system/sw/bin:/bin";
    };

    # Enable NFS client for Longhorn RWX volumes
    services.rpcbind.enable = true;

  environment.systemPackages = [
    pkgs.ghostty.terminfo
    pkgs.bash
    pkgs.nfs-utils
    pkgs.jq
  ];

   sops = {
     defaultSopsFile = "${self}/secrets.yaml";
     useSystemdActivation = true;
     secrets."k3s-token" = {
       format = "yaml";
     };
     environment = {
       SOPS_AGE_SSH_PRIVATE_KEY_FILE = "/etc/ssh/ssh_host_ed25519_key";
     };
   };
}
