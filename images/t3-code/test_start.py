import socket
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import start


class ForwarderStartup(unittest.TestCase):
    def test_waits_until_the_listener_accepts(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            self.assertTrue(start.wait_for_port(listener.getsockname()[1], timeout=5))

    def test_gives_up_when_nothing_listens(self):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        self.assertFalse(start.wait_for_port(port, timeout=0.2))

    def test_launches_the_runtime_copy_of_the_forwarder(self):
        with patch.object(start.subprocess, 'Popen') as popen:
            start.start_forwarder(Path('/etc/t3-code/runtime'))
        command = popen.call_args.args[0]
        self.assertEqual(command[1], '/etc/t3-code/runtime/forward-forgejo.py')


class Startup(unittest.TestCase):
    def test_relays_forgejo_before_configuring_anything(self):
        """Shells in the pod and T3 itself reach Forgejo under its public name,
        which only this pod answers, so the relay comes up first."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        events = []
        with patch.object(start.Path, 'home', return_value=Path(temp.name)), \
                patch.object(start, 'start_forwarder',
                             side_effect=lambda scripts: events.append('forwarder')), \
                patch.object(start, 'wait_for_port',
                             side_effect=lambda port: events.append(('wait', port)) or True), \
                patch.object(start.runpy, 'run_path',
                             side_effect=lambda *args, **kwargs: events.append('configure')), \
                patch.object(start.os, 'execv',
                             side_effect=lambda *args: events.append('supervise')):
            start.main()
        self.assertEqual(events, ['forwarder', ('wait', start.FORGEJO_TLS_PORT),
                                  'configure', 'supervise'])


if __name__ == '__main__':
    unittest.main()
