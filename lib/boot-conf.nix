{lib, ...}: {
  config = {
    boot.loader.systemd-boot.enable = true;
    boot.loader.systemd-boot.editor = false;
    boot.loader.systemd-boot.consoleMode = "0";
    boot.loader.systemd-boot.configurationLimit = 5;
    boot.loader.timeout = 0;

    boot.initrd.systemd.enable = true;
    boot.initrd.compressor = "zstd";

    boot.tmp.useTmpfs = true;
    boot.tmp.tmpfsSize = "50%";

    boot.consoleLogLevel = 0;

    boot.kernelParams = [
      "quiet"
      "fastboot"
      "loglevel=3"
      "rd.systemd.show_status=auto"
    ];
  };
}
