{lib, pkgs, ...}: {
  config = {
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