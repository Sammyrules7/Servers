{ lib, self, config, ... }:

let
  cfg = config.fluxcd;
in

{
  options.fluxcd = with lib; {
    enable = mkEnableOption "FluxCD GitOps (CLI only - use nix-shell for bootstrap)";

    repoPath = mkOption {
      type = types.path;
      default = "${self}/examples/fluxcd";
      description = "Path to FluxCD example configurations in this repo";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ ];
  };
}