{
  pkgs,
  self,
  config,
  lib,
  ...
}:
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
    ./zram.nix
    ./kubernetes/k3s.nix
    ./kubernetes/longhorn.nix
  ];

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
