{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  k3s.enable = true;
  k3s.role = "master";
  k3s.serverAddr = "https://100.74.161.102:6443";
  tailscale.enable = true;

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server4";

deploy.host = "192.168.1.14";

  }
