"""Bootstrap the persistent home, answer the public Forgejo name, then supervise."""
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import time

FORGEJO_TLS_PORT = 443
READY_TIMEOUT = 60


def wait_for_port(port, timeout=READY_TIMEOUT, host='127.0.0.1'):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def start_forwarder(scripts):
    """Relay the public Forgejo name before the logins that rely on it are set up."""
    return subprocess.Popen([sys.executable, str(scripts / 'forward-forgejo.py')])


def main():
    home = Path.home()
    for directory in (home, home / '.codex', home / '.config/direnv',
                      home / '.config/opencode', home / '.local/share/opencode',
                      Path('/data/workspace')):
        directory.mkdir(parents=True, exist_ok=True)
    for path, content in ((home / '.bashrc', '. /etc/bashrc\n'),
                          (home / '.config/direnv/direnvrc', 'source /etc/direnv/direnvrc\n')):
        if not path.exists():
            path.write_text(content)
    scripts = Path(__file__).resolve().parent
    start_forwarder(scripts)
    # `fj auth` and T3 both reach Forgejo under its public name, which this pod
    # answers itself, so the relay has to be up before either is configured.
    if not wait_for_port(FORGEJO_TLS_PORT):
        print('The Forgejo forwarder is not listening; continuing without it', flush=True)
    runpy.run_path(str(scripts / 'setup-clis.py'), run_name='__main__')
    os.execv('/bin/python3', ['/bin/python3', str(scripts / 'runtime.py')])


if __name__ == '__main__':
    main()
