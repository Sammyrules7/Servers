{...}: {
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
      ChallengeResponseAuthentication = false;
    };
  };

  networking.firewall.allowedTCPPorts = [ 22 ];

  services.fail2ban = {
    enable = true;
    maxretry = 3;
    bantime = "1d";
    ignoreIP = [
      "127.0.0.1/8"
      "::1"
    ];
  };
}
