{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server4";

  deploy.host = "server4";
}
