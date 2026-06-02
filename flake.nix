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
    deploy-rs.url = "github:serokell/deploy-rs";
    deploy-rs.inputs.nixpkgs.follows = "nixpkgs";
    sops-nix.url = "github:Mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-stable,
      deploy-rs,
      sops-nix,
      ...
    }:
    let
      deployModule = import ./lib/deploy.nix { inherit deploy-rs self; };
      commonModules = [
        sops-nix.nixosModules.sops
      ];
    in
    {
      nixosConfigurations = {
        server1 = nixpkgs.lib.nixosSystem {
          modules = commonModules ++ [ ./hosts/server1 ];
          specialArgs = { inherit self; };
        };
        server2 = nixpkgs.lib.nixosSystem {
          modules = commonModules ++ [ ./hosts/server2 ];
          specialArgs = { inherit self; };
        };
        server3 = nixpkgs.lib.nixosSystem {
          modules = commonModules ++ [ ./hosts/server3 ];
          specialArgs = { inherit self; };
        };
        server4 = nixpkgs.lib.nixosSystem {
          modules = commonModules ++ [ ./hosts/server4 ];
          specialArgs = { inherit self; };
        };
      };

      deploy.nodes = deployModule;

      checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) deploy-rs.lib;
    };
}
