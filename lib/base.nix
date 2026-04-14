{pkgs, lib, config, ...}: {
  imports = [
    ./deployment.nix
    ./user-auth.nix
    ./net-conf.nix
    ./boot-conf.nix
    ./ssh-fail2ban.nix
    ./sys-conf.nix
    ./nix-gc.nix
    ./nix.nix
  ];

  options.k3s = {
    enable = lib.mkEnableOption "k3s Kubernetes";
    role = lib.mkOption {
      type = lib.types.enum ["master" "agent"];
      default = "master";
      description = "K3s role";
    };
    clusterInit = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Initialize embedded etcd cluster (first master only)";
    };
    serverAddr = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "K3s server address for additional masters/agents";
    };
    flannelIface = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Flannel interface (e.g. tailscale0 for Tailscale)";
    };
  };

  options.tailscale = {
    enable = lib.mkEnableOption "Tailscale VPN";
  };

  config = lib.mkMerge [
    (lib.mkIf config.k3s.enable {
      services.k3s = {
        enable = true;
        package = pkgs.k3s;
        clusterInit = config.k3s.clusterInit;
        serverAddr = config.k3s.serverAddr;
        extraFlags = lib.mkIf (config.k3s.flannelIface != "") [ "--flannel-iface=${config.k3s.flannelIface}" ];
      };
      environment.sessionVariables = {
        KUBECONFIG = "/etc/rancher/k3s/k3s.yaml";
      };
    })
    (lib.mkIf config.tailscale.enable {
      services.tailscale = {
        enable = true;
      };
    })
    {
      environment.systemPackages = [
        pkgs.ghostty.terminfo
      ];
    }
  ];
}