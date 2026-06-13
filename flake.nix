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
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-24.11";
    colmena.url = "github:zhaofengli/colmena";
    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-stable,
      colmena,
      sops-nix,
      ...
    }:
    let
      commonModules = [
        sops-nix.nixosModules.sops
      ];
    in
    {
      # Colmena Fleet Configuration
      colmena = {
        meta = {
          nixpkgs = import nixpkgs { system = "x86_64-linux"; };
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
    };
}
