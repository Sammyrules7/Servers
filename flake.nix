{
  description = "NixOS cluster configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-stable.url = "github:NixOS/nixpkgs/nixos-24.11";
    deploy-rs.url = "github:serokell/deploy-rs";
    deploy-rs.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ {
    self,
    nixpkgs,
    nixpkgs-stable,
    deploy-rs,
    ...
  }: let
    deployModule = import ./lib/deploy.nix { inherit deploy-rs self; };
  in {
    nixosConfigurations = {
      server1 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server1 ];
        specialArgs = { inherit self; };
      };
      server2 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server2 ];
        specialArgs = { inherit self; };
      };
      server3 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server3 ];
        specialArgs = { inherit self; };
      };
      server4 = nixpkgs.lib.nixosSystem {
        modules = [ ./hosts/server4 ];
        specialArgs = { inherit self; };
      };
    };

    deploy.nodes = deployModule;

    checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) deploy-rs.lib;
  };
}