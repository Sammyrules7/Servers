{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server1";

  deploy.host = "server1";

  k3s.enable = true;
  k3s.role = "server";
  k3s.nodeIP = "100.74.161.102";
  k3s.nodeLabels = {
    "topology.kubernetes.io/zone" = "home";
  };
}
