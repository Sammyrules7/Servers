{pkgs, ...}: {
  imports = [
    ./deployment.nix
    ./user-auth.nix
    ./net-conf.nix
    ./boot-conf.nix
    ./ssh-fail2ban.nix
    ./sys-conf.nix
    ./nix-gc.nix
    ./nix.nix
  ];

  environment.systemPackages = [
    pkgs.ghostty.terminfo
  ];
}
