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
      "dm_multipath"
      "iscsi_tcp"
      "iscsi_target_mod"
      "target_core_mod"
    ];

  services.openiscsi = {
    enable = true;
    name = "iqn.2016-04.com.open-iscsi:${config.networking.hostName}";
  };

  environment.systemPackages = [
    pkgs.ghostty.terminfo
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
