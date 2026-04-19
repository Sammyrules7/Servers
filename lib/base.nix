{pkgs, ...}: {
  imports = [
    ./deployment.nix
    ./user-auth.nix
    ./net-conf.nix
    ./boot-conf.nix
    ./ssh.nix
    ./sys-conf.nix
    ./nix-gc.nix
    ./nix.nix
    ./tailscale.nix
  ];

  environment.systemPackages = [
    pkgs.ghostty.terminfo
  ];
}
