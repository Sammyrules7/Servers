{lib, ...}: {
  options.deploy.host = lib.mkOption {
    type = lib.types.str;
    description = "IP or hostname for deployment";
  };

  config = {
    users.users.deploy = {
      isNormalUser = true;
      extraGroups = ["wheel"];
      password = "";
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICBbJZYAoaiso9r80YdbBkqFZ1bggET4EEkzZ9ckBbGW"
      ];
    };

    nix.settings.trusted-users = ["root" "deploy" "@wheel"];
  };
}
