{lib, ...}: {
  nix.gc.automatic = lib.mkDefault true;
  nix.gc.dates = "weekly";
  nix.gc.options = "--delete-older-than 30d";

  systemd.services.nix-gc.serviceConfig = {
    Nice = 19;
    IOSchedulingClass = "best-effect";
    IOSchedulingPriority = 7;
  };
}