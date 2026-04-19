{...}: {
  config = {
    security.sudo.enable = true;
    security.sudo.wheelNeedsPassword = false;

    users.users.sammy = {
      isNormalUser = true;
      extraGroups = ["wheel"];
      openssh.authorizedKeys.keys = [
        # desktop
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICBbJZYAoaiso9r80YdbBkqFZ1bggET4EEkzZ9ckBbGW"
        # laptop
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICvbJQ3KnO165S9pyfQ5qHXFv51cw3LmsvUn6Xo2Bbr7"
      ];
    };

    users.users.deploy = {
      isNormalUser = true;
      extraGroups = ["wheel"];
      openssh.authorizedKeys.keys = [
        # desktop
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICBbJZYAoaiso9r80YdbBkqFZ1bggET4EEkzZ9ckBbGW"
        # laptop
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICvbJQ3KnO165S9pyfQ5qHXFv51cw3LmsvUn6Xo2Bbr7"
      ];
    };
  };
}
