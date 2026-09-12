{
  description = "NixOS cluster configuration";

  nixConfig = {
    extra-substituters = [
      "https://attic.maio-tech.com/main"
    ];
    extra-trusted-public-keys = [
      "main:arW6XEJpG5vVm3SeAKZ4gohKH6xAKRN2E02iz6vgbXE="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    colmena.url = "github:zhaofengli/colmena";
    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
    nix-snapshotter.url = "github:pdtpartners/nix-snapshotter";
    nix-snapshotter.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      colmena,
      sops-nix,
      nix-snapshotter,
      ...
    }:
    let
      system = "x86_64-linux";
      commonModules = [
        sops-nix.nixosModules.sops
        nix-snapshotter.nixosModules.default
      ];
    in
    {
      # Colmena Fleet Configuration
      colmena = {
        meta = {
          nixpkgs = import nixpkgs { inherit system; };
          specialArgs = { inherit self; };
        };

        server1 = {
          deployment = {
            targetHost = "server1";
            targetUser = "deploy";
          };
          imports = commonModules ++ [ ./hosts/server1 ];
        };

        server2 = {
          deployment = {
            targetHost = "server2";
            targetUser = "deploy";
            targetPort = 2222;
          };
          imports = commonModules ++ [ ./hosts/server2 ];
        };

        server3 = {
          deployment = {
            targetHost = "server3";
            targetUser = "deploy";
          };
          imports = commonModules ++ [ ./hosts/server3 ];
        };

        server4 = {
          deployment = {
            targetHost = "server4";
            targetUser = "deploy";
          };
          imports = commonModules ++ [ ./hosts/server4 ];
        };
      };

      # Required for modern flake-compatible Colmena deployments
      colmenaHive = colmena.lib.makeHive self.outputs.colmena;

      # Force evaluation of every host during `nix flake check --no-build`.
      checks.${system} = builtins.mapAttrs (
        _: node: node.config.system.build.toplevel
      ) self.colmenaHive.nodes;

      # Keep the deployment CLI pinned to the same Colmena revision as the
      # hive instead of resolving github:zhaofengli/colmena on every run.
      apps.${system}.colmena = colmena.apps.${system}.colmena // {
        meta.description = "Deploy the NixOS cluster with Colmena";
      };
      packages.${system}.colmena = colmena.packages.${system}.colmena;
    };
}
