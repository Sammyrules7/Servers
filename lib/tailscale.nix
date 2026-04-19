{lib, ...}: {
  config = {
    services.tailscale.enable = lib.mkDefault true;
    services.tailscale.extraSetFlags = ["--ssh"];
    networking.firewall.trustedInterfaces = ["tailscale*"];
    networking.firewall.allowedUDPPorts = [4163];
  };
}