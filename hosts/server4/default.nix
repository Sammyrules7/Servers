{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server4";

  deploy.host = "192.168.1.14";
}
