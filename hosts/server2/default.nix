{
  lib,
  pkgs,
  ...
}: {
  imports = [
    ../../lib/base.nix
    ./hardware.nix
  ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server2";

  deploy.host = "server2";

  services.openssh.ports = [
    22
    2222
  ];
  networking.firewall.allowedTCPPorts = [ 2222 ];

  # The path to this node cannot carry Tailscale's default 1280-byte MTU.
  # Configuring networking.interfaces.tailscale0 is not sufficient because
  # tailscaled recreates the interface after network setup. Reapply the MTU
  # whenever tailscaled starts so large SSH packets do not get black-holed.
  systemd.services.tailscale-mtu = {
    description = "Set the server2 Tailscale MTU";
    after = [ "tailscaled.service" ];
    requires = [ "tailscaled.service" ];
    partOf = [ "tailscaled.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig.Type = "oneshot";
    script = ''
      for attempt in {1..30}; do
        if ${pkgs.iproute2}/bin/ip link set dev tailscale0 mtu 1160; then
          exit 0
        fi
        sleep 1
      done
      exit 1
    '';
  };
  systemd.timers.tailscale-mtu = {
    description = "Periodically enforce the server2 Tailscale MTU";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "1min";
      OnUnitActiveSec = "1min";
      Unit = "tailscale-mtu.service";
    };
  };

  k3s.enable = true;
  k3s.role = "agent";
  k3s.nodeIP = "100.86.214.46";
  k3s.nodeLabels = {
    "topology.kubernetes.io/zone" = "alt";
  };

  zramSwap = lib.mkDefault {
    algorithm = "lz4";
    memoryPercent = 75;
  };

  # Old machine is legacy only boot
  boot.loader = lib.mkForce {
    systemd-boot.enable = false;
    grub.enable = true;
    grub.device = "/dev/sda";
    grub.default = "0";
    grub.extraConfig = ''
      set timeout=0
      set timeout_style=hidden
    '';
  };
}
