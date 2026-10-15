{lib, pkgs, ...}: {
  config = {
    # Bound persistent logs without increasing journal flush frequency.
    services.journald.settings.Journal = {
      SystemMaxUse = "256M";
      RuntimeMaxUse = "64M";
      MaxRetentionSec = "7day";
    };

    # Defaults for service-owned file logs; kubelet rotates CRI logs itself.
    services.logrotate.settings.header = {
      weekly = true;
      rotate = 4;
      compress = true;
      delaycompress = true;
    };

    time.timeZone = lib.mkDefault "UTC";

    i18n.defaultLocale = "en_US.UTF-8";

    console = {
      font = "lat9w-16";
      keyMap = "us";
    };

    environment.systemPackages = with pkgs; [
      btop
      git
      nano
    ];

    programs.bash.enable = true;

    system.stateVersion = lib.mkDefault "24.11";
  };
}