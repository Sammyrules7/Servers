"""Install current npm channels atomically and supervise the headless server."""
import json
import base64
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import tarfile
import urllib.request

RUNTIME = Path(os.environ.get("T3CODE_RUNTIME_DIR", "/data/runtime"))
INTERVAL = int(os.environ.get("T3CODE_UPDATE_INTERVAL_SECONDS", "3600"))
child = None
OPENCODE_PACKAGE = "@opencode/cli"
OPENCODE_PLATFORM = "@opencode/cli-linux-x64-baseline"
MINIMUM_OPENCODE = (2, 0, 18)


def metadata(package, version):
    with urllib.request.urlopen(f"https://registry.npmjs.org/{package}/{version}", timeout=30) as response:
        return json.load(response)


def install_opencode(stage, version):
    package = metadata(OPENCODE_PLATFORM, version)
    if package["version"] != version:
        raise ValueError("OpenCode platform version does not match requested release")
    integrity = package["dist"]["integrity"]
    if not integrity.startswith("sha512-"):
        raise ValueError("OpenCode archive requires SHA-512 integrity")
    expected = base64.b64decode(integrity.removeprefix("sha512-"), validate=True)
    archive = stage / "opencode.tgz"
    digest = hashlib.sha512()
    with urllib.request.urlopen(package["dist"]["tarball"], timeout=120) as response, archive.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
    if digest.digest() != expected:
        raise ValueError("OpenCode archive checksum mismatch")
    target = stage / "bin/opencode"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as contents:
        binary = contents.getmember("package/bin/opencode")
        if not binary.isfile():
            raise ValueError("OpenCode archive does not contain a regular executable")
        with contents.extractfile(binary) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
    target.chmod(0o755)
    archive.unlink()
    binary_link = stage / "node_modules/.bin/opencode"
    binary_link.parent.mkdir(parents=True, exist_ok=True)
    binary_link.unlink(missing_ok=True)
    binary_link.symlink_to("../../bin/opencode")


def refresh():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    with (RUNTIME / "update.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return refresh_locked()


def refresh_locked():
    versions = {}
    for package, tag in (("t3", "nightly"), ("@openai/codex", "latest"),
                         (OPENCODE_PACKAGE, "latest")):
        versions[package] = metadata(package, tag)["version"]
    opencode_version = versions[OPENCODE_PACKAGE]
    parts = opencode_version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts) or tuple(map(int, parts)) < MINIMUM_OPENCODE:
        raise ValueError(f"T3 requires stable OpenCode >= 2.0.18; registry returned {opencode_version}")
    current = RUNTIME / "current"
    if (current / "versions.json").exists():
        if json.loads((current / "versions.json").read_text()) == versions:
            return False
    RUNTIME.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="release-", dir=RUNTIME))
    try:
        subprocess.run([
            "npm", "install", "--prefix", str(stage), "--no-audit", "--no-fund",
            "--ignore-scripts", f"t3@{versions['t3']}", f"@openai/codex@{versions['@openai/codex']}",
        ], check=True, timeout=900)
        install_opencode(stage, opencode_version)
        # A release must run in this Nix environment before replacing the current one.
        for binary in ("t3", "codex", "opencode"):
            result = subprocess.run([str(stage / "node_modules/.bin" / binary), "--version"], check=True, timeout=60,
                                    capture_output=True, text=True)
            if binary == "opencode" and result.stdout.strip().removeprefix("opencode v") != opencode_version:
                raise ValueError("OpenCode executable version does not match release metadata")
        (stage / "versions.json").write_text(json.dumps(versions))
        link = RUNTIME / "next"
        link.unlink(missing_ok=True)
        link.symlink_to(stage.name)
        link.replace(current)
        print(f"Installed {versions}", flush=True)
        return True
    except BaseException:
        shutil.rmtree(stage)
        raise


def stop():
    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def terminate(signum, frame):
    stop()
    sys.exit(0)


def main():
    global child
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        refresh()
    except Exception as error:
        if "--update-only" in sys.argv:
            raise
        if not (RUNTIME / "current/versions.json").exists():
            raise
        print(f"Update unavailable; using cached release: {error}", flush=True)
    if "--update-only" in sys.argv:
        return
    while True:
        child = subprocess.Popen([
            str(RUNTIME / "current/node_modules/.bin/t3"), "serve", "--host", "0.0.0.0",
            "--port", os.environ.get("T3CODE_PORT", "3773"), "/workspace",
        ])
        while True:
            try:
                status = child.wait(timeout=INTERVAL)
                sys.exit(status or 1)
            except subprocess.TimeoutExpired:
                try:
                    changed = refresh()
                except Exception as error:
                    print(f"Update unavailable; keeping current release: {error}", flush=True)
                    continue
                if changed:
                    stop()
                    # Retain only the installed release; npm's persistent cache avoids re-downloads.
                    active = (RUNTIME / "current").resolve()
                    for release in RUNTIME.glob("release-*"):
                        if release != active:
                            shutil.rmtree(release)
                    break


if __name__ == "__main__":
    main()
