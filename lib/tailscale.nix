{config, lib, ...}: {
  config = {
    services.tailscale.enable = lib.mkDefault true;
    services.tailscale.extraSetFlags = ["--ssh" "--advertise-exit-node"];
    services.tailscale.useRoutingFeatures = "server";
    networking.firewall.trustedInterfaces = ["tailscale0"];
    networking.firewall.allowedUDPPorts = [config.services.tailscale.port];
  };
}
