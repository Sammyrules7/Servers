{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  k3s.enable = true;
  k3s.role = "agent";
  k3s.serverAddr = "https://192.168.1.11:6443";
  tailscale.enable = true;

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server2";

  deploy.host = "192.168.1.12";

  sops = {
    defaultSopsFile = ../../secrets/k3s.yaml;
    age.sshKeyPaths = [ "/etc/ssh/ssh_host_ed25519_key" ];
    secrets = {
      "k3s-agent-token" = {
        key = "k3s.agent_token";
        format = "yaml";
      };
    };
  };

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
