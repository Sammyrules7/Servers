# Unfunded Lightning node

Bitcoin Core and Core Lightning run together on server1. Bitcoin Core's
authenticated RPC uses loopback and a cookie on the chain volume. Core Lightning
waits for Bitcoin Core's initial download, then uses a dedicated CloudNativePG
database for channel state. The Core Lightning RPC is a local Unix socket.
Neither process accepts public inbound connections. There is no funding or
channel-opening automation.

Bitcoin Core downloads and validates the chain, then retains about 16 GiB of
block files, in addition to chainstate and indexes. The local-path PVC sizes
are requests, not filesystem quotas. Monitor server1's free space and do not
force-delete the Lightning pod while the old process may still be running.
If Lightning misses blocks that Bitcoin Core pruned, it may require a backend
resync before Lightning can catch up.

Check Bitcoin sync and Lightning status:

```sh
kubectl -n lightning exec lightning-0 -c bitcoin -- bitcoin-cli -datadir=/bitcoin getblockchaininfo
kubectl -n lightning exec lightning-0 -c lightning -- lightning-cli --lightning-dir=/lightning getinfo
```

Keep this deployment unfunded until the wallet secret has an encrypted off-host
backup and recovery has been tested. The database has one instance and no
configured off-host backup. Before operating funded channels, configure durable
database replication that preserves committed writes and back up the static
channel recovery file separately. Garage can store encrypted recovery files.
An old database snapshot can put channel funds at risk.
