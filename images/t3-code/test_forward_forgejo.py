import importlib.util
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest

spec = importlib.util.spec_from_file_location(
    'forward_forgejo', Path(__file__).with_name('forward-forgejo.py'))
forward_forgejo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(forward_forgejo)

# Throwaway certificate and key, generated for these tests only and valid until
# 2126. It exists so the TLS listener can be exercised without a live issuer.
CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIDRTCCAi2gAwIBAgIUUkHqb9YqlrKCuprhUre2aRdtJz4wDQYJKoZIhvcNAQEL
BQAwIDEeMBwGA1UEAwwVZm9yZ2Vqby5tYWlvLXRlY2guY29tMCAXDTI2MTAxNjAw
Mjg1MloYDzIxMjYwOTIyMDAyODUyWjAgMR4wHAYDVQQDDBVmb3JnZWpvLm1haW8t
dGVjaC5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCieZbvRb8M
MxXBM4Dr47rZMeiJRM9+QVjU7gjC883u+9RYFQN7oHV9URZjFd8zl23V2szH9EYx
xQeURklqK65R+2sMqMbGCaQmhb73OcJyM21h41wNmdm96khBTuZCyDZqgNjrzvyS
VCfDccDL+Dzjjzz8et/zs2ipU+oa3C5jJX15FW9spYUJxWhoedjGaQ0X4TvAH+pT
JkUZS/qt15FvVCUpY0SIatT0n4JFgzBMZVhAKoIvlkFwrztebuLZqMEk7VtOZybf
1vAVoQ5g4mjbvRQQYEyKhFN/PAcxWl0gPX3iGztJQ1QoYrMKh46r+fP6pHHX0DKc
hIUZRkAbAtYFAgMBAAGjdTBzMB0GA1UdDgQWBBThlBb9a5qDyj2N2sAwjz6O42GV
zzAfBgNVHSMEGDAWgBThlBb9a5qDyj2N2sAwjz6O42GVzzAPBgNVHRMBAf8EBTAD
AQH/MCAGA1UdEQQZMBeCFWZvcmdlam8ubWFpby10ZWNoLmNvbTANBgkqhkiG9w0B
AQsFAAOCAQEAWCY4RamWL2sXgvyoRug3//VbiPrIvpJy6pGG0rV8JbIErHwvL9VU
Cy+q3IkRFaLFqH2j+23CNjdEWFRjifzX+YfDAJGFzMTiGAmLU5gcioUEIJrhsLvs
2E4Fp8FoEj0zjdVr6HMgTpRg6Z2YDKyDClIDC341aO2Cx9ces5CgGuhuTvFt6kLK
LaWti1ftltM0aT+qd6/6zL29NgsxyCLVNAeZUi1aR4cuDb7Vc6aGnmewpCqWQYrS
snXKtexgixNSJw4HYrKhVZzgFcSiSXzRhIufVSm7VGh1s2/C8juQPrHVlBYrnqk5
RsvJikoxMnw2NQ54tYVeC9XaCMqzJ9l9MA==
-----END CERTIFICATE-----
"""

KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCieZbvRb8MMxXB
M4Dr47rZMeiJRM9+QVjU7gjC883u+9RYFQN7oHV9URZjFd8zl23V2szH9EYxxQeU
RklqK65R+2sMqMbGCaQmhb73OcJyM21h41wNmdm96khBTuZCyDZqgNjrzvySVCfD
ccDL+Dzjjzz8et/zs2ipU+oa3C5jJX15FW9spYUJxWhoedjGaQ0X4TvAH+pTJkUZ
S/qt15FvVCUpY0SIatT0n4JFgzBMZVhAKoIvlkFwrztebuLZqMEk7VtOZybf1vAV
oQ5g4mjbvRQQYEyKhFN/PAcxWl0gPX3iGztJQ1QoYrMKh46r+fP6pHHX0DKchIUZ
RkAbAtYFAgMBAAECggEAA9+nQBQnHmjXY3BRag5XZZdBhohL9CQltInqTo+WgNSj
NuhlWVy1gGPfB0S9uhKprTgWusuxor0iVaApXu0krlKyti4N8ynGrp5ws58+ag+c
04EisDZTUSpVR61UYxI37ekdgt2/+tMj0Y6UPKix9vDy0MgzL7G+1I6qHbLTLkzs
SdwyX6vsJpCUGzQAmt324HEvwLhTViOELoTy7lJVd3+AblmVoUm/qyIadSbP4/Aw
XxkUa2K51s7uHsNG10fR6Awc3wDicyJLfaSZSS4EmWP/sbmr9mkraxpY1fgRR/pu
qmNqd9z5sCAilHJkGzNVybIFyYcfJcpv/MDZ11QQnwKBgQDUPdFlkN2XV171hp9+
vx9617RWS9BWxp6JSZmfbAgDH/dtSZbffvVzGvAcNOQ2FxWihAQ4LW90Wz2EGuQt
xCNUn5w4T0GuNZON8584k2Ch0S3yWFVTvIXXTb9nYsPptu7SEo15RxqiXbayP0uc
ywv0gWOImfeAsIOpqZR/eIIliwKBgQDD+ROq2lb9bXfJq9mQXOHnDZ7QqXbOiYX1
9/rdI0sLQ/r/0wQve23aSsWqgh4xN6yOcsHaMXo9ouA81/9tJh/k9wTM9izaEJ+F
3DJX7ZHeuymeckTbyp0cOGgShm6Ywma7Z6p0DonC5X0ceCwLLUnqAW+Gw/blDed/
kp5nZP8ErwKBgA1CJ1iO6ijQHnB8Dm6ehdroqq1RYxxon/K3lE8vMnjvgEdld3VS
uwaLwkAg1bjDTGiwkorn27SLFpawD10Eiah5qAqkeNfnJOaTN3kTS9AP/yzKc9od
RsciZjiRJOfus5CP9CKFXJaUABu2dITA8mg9xPf9lkaFwFPS8iHcZ1TtAoGAcxkn
9vGzo7aWYyj+Z+5Vc1mpjA3rzFQzDIqvmQ+wdJZhpbzuuWB53XqK66DuUKPNQgCe
YCMtE2RE5RdLWnTIyLZX6HUxVIXs2za/jqrmQHWWdQvR63Dto3Rxk2fHLwsGQU0a
bH1ZZdFZEM53t7zKq5haQ0F3EYKAE4ouZLWJndsCgYEAlKzl/Kas89KxQnGU8svH
ILIGcZXmoUk+afK5D8j2cbk4eOe9ZbXEGpLzVrTZPNDFXxdWz9Z4cDiJYS2QKwEv
vC2ddQ4OAZnIX3477RGgd0XwQic+1wbcY9XfPA6CBxOsAWBATvRlrFmSKMLEev9F
ifxrjH+mmkE8Pk2WEbdllsM=
-----END PRIVATE KEY-----
"""


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


def wait_for_port(port, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.05)
    return False


class FakeForgejo:
    """Echo anything received, standing in for the Forgejo service."""

    def __init__(self):
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('127.0.0.1', 0))
        self.server.listen(8)
        self.port = self.server.getsockname()[1]
        threading.Thread(target=self.accept, daemon=True).start()

    def accept(self):
        while True:
            try:
                client, _ = self.server.accept()
            except OSError:
                return
            threading.Thread(target=self.echo, args=(client,), daemon=True).start()

    def echo(self, client):
        try:
            while chunk := client.recv(4096):
                client.sendall(chunk)
        except OSError:
            pass
        finally:
            client.close()

    def close(self):
        self.server.close()


class Forwarding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plain = free_port()
        self.tls = free_port()
        self.upstream = FakeForgejo()
        self.addCleanup(self.upstream.close)
        (self.root / 'tls.crt').write_text(CERTIFICATE)
        (self.root / 'tls.key').write_text(KEY)

    def start(self, issued=True):
        certificate = 'tls' if issued else 'missing'
        forwarder = subprocess.Popen([
            sys.executable, str(Path(__file__).with_name('forward-forgejo.py')),
            '--upstream', f'127.0.0.1:{self.upstream.port}',
            '--bind', '127.0.0.1',
            '--plain-port', str(self.plain),
            '--tls-port', str(self.tls),
            '--cert', str(self.root / f'{certificate}.crt'),
            '--key', str(self.root / f'{certificate}.key'),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(forwarder.kill)
        self.assertTrue(wait_for_port(self.plain), 'the plaintext listener did not start')
        return forwarder

    def echo(self, port, payload):
        with socket.create_connection(('127.0.0.1', port), timeout=10) as client:
            client.sendall(payload)
            return client.recv(4096)

    def test_plaintext_git_and_api_traffic_reaches_forgejo(self):
        self.start()
        self.assertEqual(self.echo(self.plain, b'GET /api/v1/version'),
                         b'GET /api/v1/version')

    def test_https_traffic_is_terminated_with_the_issued_certificate(self):
        """`fj` builds https for a bare hostname and Forgejo advertises https
        clone and LFS URLs, so the pod has to present a trusted certificate."""
        self.start()
        self.assertTrue(wait_for_port(self.tls), 'the TLS listener did not start')
        context = ssl.create_default_context(cafile=str(self.root / 'tls.crt'))
        with socket.create_connection(('127.0.0.1', self.tls), timeout=10) as raw:
            with context.wrap_socket(raw, server_hostname='forgejo.maio-tech.com') as client:
                client.sendall(b'fj auth list')
                self.assertEqual(client.recv(4096), b'fj auth list')

    def test_missing_certificate_keeps_everything_else_serving(self):
        """A certificate that has not been issued yet must not take Git or T3
        down with it; the TLS listener reports the failure and retries."""
        forwarder = self.start(issued=False)
        self.assertFalse(wait_for_port(self.tls, timeout=1))
        self.assertEqual(self.echo(self.plain, b'still serving'), b'still serving')
        self.assertIsNone(forwarder.poll(), 'the forwarder should keep retrying')


class Arguments(unittest.TestCase):
    def test_endpoint_requires_a_port(self):
        with self.assertRaises(Exception):
            forward_forgejo.endpoint('forgejo-http.forgejo.svc.cluster.local')
        self.assertEqual(forward_forgejo.endpoint('forgejo-http.forgejo.svc.cluster.local:3000'),
                         ('forgejo-http.forgejo.svc.cluster.local', 3000))

    def test_defaults_answer_the_public_name_from_the_pod(self):
        options = forward_forgejo.parse([])
        self.assertEqual(options.bind, '127.0.0.1')
        self.assertEqual((options.plain_port, options.tls_port), (80, 443))
        self.assertEqual(options.upstream,
                         ('forgejo-http.forgejo.svc.cluster.local', 3000))


if __name__ == '__main__':
    unittest.main()
