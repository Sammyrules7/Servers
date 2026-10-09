{ lib, config, sops, self, ... }:
let
  cfg = config.k3s;
  isBootstrapMaster = config.networking.hostName == "server1";
  sopsTokenPath = config.sops.secrets."k3s-token".path or null;
  # SOPS token takes precedence over manual tokenFile
  effectiveTokenFile = if sopsTokenPath != null then sopsTokenPath else cfg.tokenFile;
in {
  options.k3s = with lib; {
    enable = mkEnableOption "k3s cluster node";

    role = mkOption {
      type = types.enum [ "server" "agent" ];
      default = "server";
      description = "k3s role — server (control plane) or agent (worker)";
    };

    tokenFile = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Path to file containing cluster token (optional — SOPS secret preferred)";
    };

    bootstrapMaster = mkOption {
      type = types.str;
      default = "100.74.161.102";
      description = "IP of initial server (used by non-bootstrap nodes to join)";
    };

    nodeIP = mkOption {
      type = types.str;
      default = "";
      description = "IP address k3s binds to (usually Tailscale IP)";
    };

    nodeLabels = mkOption {
      type = types.attrsOf types.str;
      default = {};
      description = "Node labels to apply (e.g., topology.kubernetes.io/zone)";
    };
  };

   config = lib.mkIf cfg.enable {
    # Keep the image and its runtime closure alive on every schedulable node.
    environment.etc."t3-code/image".source = self.packages.x86_64-linux.t3-code-image;
    users.groups.t3-code.gid = 1773;
    users.users.t3-code = {
      isSystemUser = true;
      uid = 1773;
      group = "t3-code";
    };
    systemd.tmpfiles.rules = [ "d /nix/var/nix/gcroots/t3-code 0750 t3-code t3-code -" ];
    services.k3s = {
      enable = true;
      # k3s 1.35 supports wiring nix-snapshotter into its embedded containerd.
      # Existing OCI images continue to work through the snapshotter's fallback.
      snapshotter = "nix";
      # Add custom options here
      inherit (cfg) role;
    }
    // lib.optionalAttrs (cfg.nodeIP != "") {
      nodeIP = cfg.nodeIP;
    }
    // lib.optionalAttrs (!isBootstrapMaster && effectiveTokenFile != null) {
      tokenFile = effectiveTokenFile;
    }
    // lib.optionalAttrs (!isBootstrapMaster) {
      serverAddr = "https://${cfg.bootstrapMaster}:6443";
    }
    // lib.optionalAttrs isBootstrapMaster {
      clusterInit = true;
    }
    // lib.optionalAttrs (cfg.role == "server") {
      disable = [ "traefik" ];
    };

    environment.etc."rancher/k3s/config.yaml".text = lib.mkMerge [
      ''
        flannel-iface: tailscale0
      ''
      (lib.optionalString (cfg.nodeLabels != {})
        (let
          labelPairs = lib.mapAttrsToList (name: value: "${name}=${value}") cfg.nodeLabels;
        in ''

        node-label:
        ${lib.concatMapStringsSep "\n" (l: "  - ${l}") labelPairs}
        ''))
    ];

    services.nix-snapshotter.enable = true;

    # Ensure the CRI image-service socket exists before k3s starts.
    systemd.services.k3s = lib.mkMerge [
      {
        after = [ "nix-snapshotter.service" ];
        requires = [ "nix-snapshotter.service" ];
      }
      (lib.mkIf (sopsTokenPath != null && !isBootstrapMaster) {
        after = [ "sops-install-secrets.service" ];
        requires = [ "sops-install-secrets.service" ];
      })
    ];
  };
}
