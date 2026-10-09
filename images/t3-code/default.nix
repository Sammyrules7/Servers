{ pkgs }:
let
  inherit (pkgs) lib;
  # Provider processes inherit approved .envrc files even without an interactive shell.
  codexWithDirenv = pkgs.writeShellScriptBin "codex" ''
    exec ${pkgs.direnv}/bin/direnv exec "$(pwd -P)" /data/runtime/current/node_modules/.bin/codex "$@"
  '';
  t3 = pkgs.writeShellScriptBin "t3" ''
    exec /data/runtime/current/node_modules/.bin/t3 "$@"
  '';
  fj = pkgs.writeShellScriptBin "fj" ''
    for arg in "$@"; do
      case "$arg" in
        -H|--host|--host=*|-H?*) exec ${pkgs.forgejo-cli}/bin/fj "$@" ;;
      esac
    done
    exec ${pkgs.forgejo-cli}/bin/fj -H forgejo.maio-tech.com "$@"
  '';
  tools = pkgs.buildEnv {
    name = "t3-code-tools";
    paths = [ t3 codexWithDirenv fj pkgs.tea pkgs.gh pkgs.nix pkgs.direnv pkgs.nix-direnv
      pkgs.bashInteractive pkgs.coreutils pkgs.procps pkgs.findutils pkgs.gnugrep
      pkgs.gnused pkgs.git pkgs.git-lfs pkgs.openssh pkgs.curl pkgs.cacert pkgs.ripgrep
      pkgs.jq pkgs.nodejs_24 pkgs.python3 pkgs.gnutar pkgs.gzip ];
    pathsToLink = [ "/bin" "/share/nix-direnv" ];
  };
  # Upstream npm binaries use the conventional ELF loader and dynamically load
  # native addons. Keep this ABI available without patching every nightly build.
  libraryPath = lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.glibc
    pkgs.openssl pkgs.glib pkgs.libsecret pkgs.ncurses pkgs.zlib pkgs.libxcrypt ];
  root = pkgs.runCommand "t3-code-root" {} ''
    mkdir -p $out/etc/nix $out/etc/direnv $out/bin $out/usr/bin $out/tmp $out/data $out/lib64
    mkdir -p $out/nix/store $out/nix/var/nix/daemon-socket $out/nix/var/nix/gcroots/t3-code $out/dev $out/proc
    ln -s /bin/env $out/usr/bin/env
    ln -s /data/workspace $out/workspace
    ln -s ${pkgs.glibc}/lib/ld-linux-x86-64.so.2 $out/lib64/ld-linux-x86-64.so.2
    ln -s lib64 $out/lib
    ln -s ${tools}/bin/* $out/bin/
    cat > $out/etc/passwd <<'EOF'
    root:x:0:0:root:/root:/bin/bash
    t3-code:x:1773:1773:T3 Code:/data/home:/bin/bash
    EOF
    printf 'root:x:0:\nt3-code:x:1773:\n' > $out/etc/group
    printf 'hosts: files dns\n' > $out/etc/nsswitch.conf
    cat > $out/etc/nix/nix.conf <<'EOF'
    experimental-features = nix-command flakes
    substituters = https://cache.nixos.org https://attic.maio-tech.com/main
    trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= main:arW6XEJpG5vVm3SeAKZ4gohKH6xAKRN2E02iz6vgbXE=
    EOF
    cat > $out/etc/direnv/direnvrc <<'EOF'
    source ${pkgs.nix-direnv}/share/nix-direnv/direnvrc
    direnv_layout_dir() {
      local project_hash
      project_hash=$(printf '%s' "$PWD" | sha256sum | cut -d ' ' -f 1)
      echo "/nix/var/nix/gcroots/t3-code/$project_hash"
    }
    EOF
    cat > $out/etc/bashrc <<'EOF'
    eval "$(direnv hook bash)"
    EOF
    ln -s ${pkgs.cacert}/etc/ssl $out/etc/ssl
  '';
  start = pkgs.writeShellScript "t3-code-start" ''
    set -e
    mkdir -p "$HOME" "$HOME/.codex" "$HOME/.config/direnv" /data/workspace
    if [ ! -e "$HOME/.bashrc" ]; then
      printf '. /etc/bashrc\n' > "$HOME/.bashrc"
    fi
    if [ ! -e "$HOME/.config/direnv/direnvrc" ]; then
      printf 'source /etc/direnv/direnvrc\n' > "$HOME/.config/direnv/direnvrc"
    fi
    ${pkgs.python3}/bin/python3 ${./setup-clis.py}
    exec ${pkgs.python3}/bin/python3 ${./runtime.py}
  '';
  env = [ "PATH=/bin" "HOME=/data/home" "SHELL=/bin/bash"
    "T3CODE_HOME=/data/t3" "NIX_REMOTE=daemon" "LD_LIBRARY_PATH=${libraryPath}"
    "NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
    "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt" ];
  image = pkgs.nix-snapshotter.buildImage {
    name = "t3-code";
    resolvedByNix = true;
    copyToRoot = root;
    config = {
      entrypoint = [ "${start}" ];
      user = "1773:1773";
      workingDir = "/data";
      inherit env;
      exposedPorts."3773/tcp" = {};
    };
  };
in
{ inherit image tools root start env; }
