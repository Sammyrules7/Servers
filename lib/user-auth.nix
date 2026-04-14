{...}: {
  config = {
    security.sudo.enable = true;
    security.sudo.wheelNeedsPassword = false;

    users.users.sammy = {
      isNormalUser = true;
      extraGroups = ["wheel"];
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICBbJZYAoaiso9r80YdbBkqFZ1bggET4EEkzZ9ckBbGW"
      ];
    };

    users.users.deploy = {
      isNormalUser = true;
      extraGroups = ["wheel"];
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICBbJZYAoaiso9r80YdbBkqFZ1bggET4EEkzZ9ckBbGW"
      ];
    };
  };
}
