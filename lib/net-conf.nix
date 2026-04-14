{lib, ...}: {
  config = {
    networking.hostName = lib.mkDefault "nixos-cluster";

    networking.firewall.enable = lib.mkDefault true;
    networking.firewall.trustedInterfaces = [ "tailscale0" ];
  };
}
