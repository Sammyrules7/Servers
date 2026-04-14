{deploy-rs, self}: let
  lib = deploy-rs.lib.x86_64-linux;
  getHost = name: (self.nixosConfigurations.${name}.config.deploy.host or name);
  deployKey = "/home/sammy/.ssh/id_ed25519";
  mkNode = name: {
    name = name;
    value = {
      hostname = getHost name;
      sshOpts = [
        "-o" "BatchMode=yes"
        "-o" "StrictHostKeyChecking=no"
        "-i" deployKey
      ];
      magicRollback = false;
      remoteBuild = true;
      profiles.system = {
        user = "root";
        sshUser = "deploy";
        path = lib.activate.nixos self.nixosConfigurations.${name};
      };
    };
  };
in builtins.listToAttrs (map mkNode ["server1" "server2" "server3" "server4"])
