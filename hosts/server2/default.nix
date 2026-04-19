{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server2";

  deploy.host = "server2";

  # Old machine is legacy only boot
  boot.loader = lib.mkForce {
    systemd-boot.enable = false;
    grub.enable = true;
    grub.device = "/dev/sda";
    grub.default = "0";
    grub.extraConfig = ''
      set timeout=0
      set timeout_style=hidden
    '';
  };
}
