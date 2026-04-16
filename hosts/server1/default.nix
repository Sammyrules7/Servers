{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  k3s.enable = true;
  k3s.role = "master";
  k3s.clusterInit = true;
  tailscale.enable = true;

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server1";

deploy.host = "192.168.1.11";

  }
