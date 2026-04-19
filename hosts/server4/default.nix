{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server4";

  deploy.host = "server4";

  k3s.enable = true;
  k3s.role = "server";
  k3s.nodeIP = "100.101.5.33";
}