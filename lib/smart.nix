{ config, ... }:
{
  services.smartd = {
    enable = true;
    autodetect = true;
    notifications.wall.enable = true;
    defaults.monitored = "-a -W 4,55,65";
  };

  services.prometheus.exporters.smartctl = {
    enable = true;
    # Only expose disk telemetry on the cluster's trusted Tailscale network.
    listenAddress = config.k3s.nodeIP;
    maxInterval = "5m";
  };
}
