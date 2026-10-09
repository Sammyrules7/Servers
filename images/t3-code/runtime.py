"""Install current npm channels atomically and supervise the headless server."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.request

RUNTIME = Path(os.environ.get("T3CODE_RUNTIME_DIR", "/data/runtime"))
INTERVAL = int(os.environ.get("T3CODE_UPDATE_INTERVAL_SECONDS", "3600"))
child = None


def refresh():
    versions = {}
    for package, tag in (("t3", "nightly"), ("@openai/codex", "latest")):
        with urllib.request.urlopen(f"https://registry.npmjs.org/{package}/{tag}", timeout=30) as response:
            versions[package] = json.load(response)["version"]
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
        # A release must run in this Nix environment before replacing the current one.
        for binary in ("t3", "codex"):
            subprocess.run([str(stage / "node_modules/.bin" / binary), "--version"], check=True, timeout=60)
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
