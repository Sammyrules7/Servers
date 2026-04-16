{lib, ...}: {
  imports = [ ../../lib/base.nix ./hardware.nix ];

  k3s.enable = true;
  k3s.role = "master";
  k3s.serverAddr = "https://192.168.1.11:6443";
  tailscale.enable = true;

  nixpkgs.system = "x86_64-linux";
  networking.hostName = "server4";

deploy.host = "192.168.1.14";

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
}
