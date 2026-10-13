{ pkgs }:
let
  tools = pkgs.buildEnv {
    name = "forgejo-ci-tools";
    paths = with pkgs; [ bashInteractive coreutils findutils gnugrep gnused
      gnutar gzip git openssh curl cacert nix python3 jq ];
    pathsToLink = [ "/bin" ];
  };
  root = pkgs.runCommand "forgejo-ci-root" {} ''
    mkdir -p $out/bin $out/usr/bin $out/etc/nix $out/tmp $out/data/home
    mkdir -p $out/nix/store $out/nix/var/nix/daemon-socket $out/shared/act
    ln -s ${tools}/bin/* $out/bin/
    ln -s /bin/env $out/usr/bin/env
    chmod 1777 $out/tmp
    chmod 0777 $out/data/home $out/shared $out/shared/act
    printf 'root:x:0:0:root:/root:/bin/bash\nforgejo-ci:x:1774:1774:Forgejo CI:/data/home:/bin/bash\n' > $out/etc/passwd
    printf 'root:x:0:\nforgejo-ci:x:1774:\n' > $out/etc/group
    printf 'hosts: files dns\n' > $out/etc/nsswitch.conf
    ln -s ${pkgs.cacert}/etc/ssl $out/etc/ssl
    cat > $out/etc/nix/nix.conf <<'EOF'
    experimental-features = nix-command flakes
    substituters = https://cache.nixos.org https://attic.maio-tech.com/main
    trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= main:arW6XEJpG5vVm3SeAKZ4gohKH6xAKRN2E02iz6vgbXE=
    EOF
  '';
  image = pkgs.nix-snapshotter.buildImage {
    name = "forgejo-ci";
    resolvedByNix = true;
    copyToRoot = root;
    config = {
      user = "1774:1774";
      workingDir = "/shared/act";
      env = [ "PATH=/bin" "HOME=/data/home" "NIX_REMOTE=daemon"
        "NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
        "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt" ];
      # Runner plugin can override this; keep idle without privileged services.
      cmd = [ "/bin/sleep" "infinity" ];
    };
  };
in
{ inherit tools root image; }
