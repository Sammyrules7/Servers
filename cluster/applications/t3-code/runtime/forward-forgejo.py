"""Answer Forgejo's public name from inside the pod and relay it to the service.

T3 keys a repository by the host `git remote get-url` reports, and every pull
request link is written with the public host, so the pod resolves
`forgejo.maio-tech.com` to itself (the deployment's hostAliases) instead of
rewriting Git to the in-cluster name — a rewrite makes `git remote get-url`
report a host no pull request link uses, which is what stopped T3 from reading
change requests at all.

Both listeners exist because both schemes are used inside the pod: Git and T3
speak plaintext to the cluster, while `fj` defaults to https for a bare host and
Forgejo advertises https clone and LFS URLs.
"""
import argparse
import socket
import ssl
import sys
import threading
import time

BUFFER = 1 << 16
DIAL_TIMEOUT = 30
RETRY_SECONDS = 1


def endpoint(value):
    host, _, port = value.rpartition(':')
    if not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f'{value} is not host:port')
    return host, int(port)


def relay(source, sink):
    """Copy one direction until either side stops writing."""
    try:
        while chunk := source.recv(BUFFER):
            sink.sendall(chunk)
    except OSError:
        pass
    finally:
        try:
            sink.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def context(cert, key):
    """Read the certificate per connection so a renewal is picked up."""
    if cert is None:
        return None
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    return context


def forward(client, upstream, cert, key):
    try:
        connection = socket.create_connection(upstream, timeout=DIAL_TIMEOUT)
    except OSError:
        client.close()
        return
    if cert is not None:
        try:
            client = context(cert, key).wrap_socket(client, server_side=True)
        except (OSError, ssl.SSLError):
            client.close()
            connection.close()
            return
    connection.settimeout(None)
    writer = threading.Thread(target=relay, args=(connection, client), daemon=True)
    writer.start()
    relay(client, connection)
    writer.join()
    client.close()
    connection.close()


def listen(port, bind, upstream, cert, key):
    """Accept connections until the listener fails; the caller retries."""
    # Fail before accepting when a TLS listener has no usable certificate.
    context(cert, key)
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((bind, port))
    listener.listen(64)
    print(f'forgejo forwarder listening on {bind}:{port}'
          f'{" (tls)" if cert is not None else " (plain)"} to {upstream[0]}:{upstream[1]}',
          flush=True)
    while True:
        client, _ = listener.accept()
        threading.Thread(target=forward, args=(client, upstream, cert, key), daemon=True).start()


def serve(port, bind, upstream, cert, key):
    while True:
        try:
            listen(port, bind, upstream, cert, key)
        except Exception as error:
            print(f'forgejo forwarder on {bind}:{port} unavailable: {error}', flush=True)
            time.sleep(RETRY_SECONDS)


def parse(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=endpoint,
                        default=endpoint('forgejo-http.forgejo.svc.cluster.local:3000'))
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--plain-port', type=int, default=80)
    parser.add_argument('--tls-port', type=int, default=443)
    parser.add_argument('--cert', default='/etc/t3-code/tls/tls.crt')
    parser.add_argument('--key', default='/etc/t3-code/tls/tls.key')
    return parser.parse_args(argv)


def main(argv=None):
    options = parse(sys.argv[1:] if argv is None else argv)
    for port, cert, key in ((options.plain_port, None, None),
                            (options.tls_port, options.cert, options.key)):
        threading.Thread(target=serve,
                         args=(port, options.bind, options.upstream, cert, key),
                         daemon=True).start()
    while True:
        time.sleep(3600)


if __name__ == '__main__':
    main()
