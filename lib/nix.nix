{lib, ...}: {
  nix.settings = {
    experimental-features = ["nix-command" "flakes"];
    substituters = ["https://attic.maio-tech.com/main"];
    trusted-public-keys = ["main:arW6XEJpG5vVm3SeAKZ4gohKH6xAKRN2E02iz6vgbXE="];
    max-jobs = "auto";
    cores = 0;
    build-use-substitutes = true;
    keep-derivations = true;
    keep-outputs = true;
  };
}
