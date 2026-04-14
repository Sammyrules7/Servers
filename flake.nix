{
  description = "NixOS cluster configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-24.11";
    deploy-rs.url = "github:serokell/deploy-rs";
    deploy-rs.inputs.nixpkgs.follows = "nixpkgs";
    sops-nix.url = "github:mic92/sops-nix";
    sops-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ {
    self,
    nixpkgs,
    nixpkgs-stable,
    deploy-rs,
    sops-nix,
    ...
  }: let
    deployModule = import ./lib/deploy.nix { inherit deploy-rs self; };
  in {
    nixosConfigurations = {
      server1 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server1 sops-nix.nixosModules.sops ];
        specialArgs = { inherit self; };
      };
      server2 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server2 sops-nix.nixosModules.sops ];
        specialArgs = { inherit self; };
      };
      server3 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server3 sops-nix.nixosModules.sops ];
        specialArgs = { inherit self; };
      };
      server4 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server4 sops-nix.nixosModules.sops ];
        specialArgs = { inherit self; };
      };
    };

    deploy.nodes = deployModule;

    checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) deploy-rs.lib;
  };
}