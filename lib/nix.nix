{lib, ...}: {
  nix.settings = {
    experimental-features = ["nix-command" "flakes"];
    max-jobs = "auto";
    cores = 0;
    build-use-substitutes = true;
    keep-derivations = true;
    keep-outputs = true;
  };
}