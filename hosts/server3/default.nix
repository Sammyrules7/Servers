{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server3";

  deploy.host = "server3";

  k3s.enable = true;
  k3s.role = "server";
  k3s.nodeIP = "100.119.85.83";
  k3s.nodeLabels = {
    "topology.kubernetes.io/zone" = "home";
  };
}
