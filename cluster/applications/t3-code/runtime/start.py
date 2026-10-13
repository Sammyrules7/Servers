"""Bootstrap the persistent home, then run the Git-managed supervisor."""
import os
from pathlib import Path
import runpy


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
    runpy.run_path(str(scripts / 'setup-clis.py'), run_name='__main__')
    os.execv('/bin/python3', ['/bin/python3', str(scripts / 'runtime.py')])


if __name__ == '__main__':
    main()
