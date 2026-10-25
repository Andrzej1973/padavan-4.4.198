# Zapret2 integration

This directory builds and packages the pinned `bol-van/zapret2` snapshot for
WR1200JS and prepares its Classic WebUI control.

## Firmware contents

With `CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y` the ROMFS contains:

- `/usr/sbin/nfqws2` — MIPS packet processor with Lua, zlib and netfilter
  dependencies embedded; the only dynamic dependency is the target
  `libc.so.0`;
- `/usr/sbin/zapret2` — explicit lifecycle wrapper;
- `/usr/share/zapret2/zapret-lib.lua`;
- `/usr/share/zapret2/zapret-antidpi.lua`;
- `/usr/share/zapret2/zapret-auto.lua`;
- `/usr/share/licenses/zapret2/LICENSE.txt`.

The runtime default is `zapret2_enable=0`. The WebUI field stores
`/etc/storage/zapret2.args`. The service rejects an empty strategy, missing Lua
support, an unavailable WAN interface or a strategy larger than 8192 bytes.

## Lifecycle

The wrapper supports:

```text
/usr/sbin/zapret2 start
/usr/sbin/zapret2 stop
/usr/sbin/zapret2 restart
/usr/sbin/zapret2 status
/usr/sbin/zapret2 rules
```

It owns a singleton `nfqws2` process, the `ZAPRET2` mangle chain and queue 200.
TCP/UDP rules use `--queue-bypass`. Private destinations return before the
queue. Daemon output is suppressed and no `LOG` rule is installed.

The stored PID is checked against `/proc/<pid>/cmdline`; stale or unrelated
PIDs are not killed. Process scans suppress exit-race noise.

## WebUI state

**Administration → Services** shows the saved request separately from:

- `nfqws2` process;
- complete TCP/UDP NFQUEUE chain;
- strategy-file readiness.

The “process, strategy and rules present” state does not verify blocking
effectiveness, routing or management access. Apply reuses Padavan's firewall
event and reapplies Zapret2 after the firewall is rebuilt.

## Strategy boundary

The textarea accepts arguments passed directly to `nfqws2`; it is not a shell
script. The service adds queue number 200 and all three pinned Lua init files.
Strategy behavior remains provider-, network- and protocol-specific and must be
tested with a recovery path available.

## Host checks

```text
sh tools/zapret2/test-service.sh
python tools/zapret2/prepare-web.py <pinned-padavan-tree>
python tools/zapret2/check-web.py <pinned-padavan-tree> --node
python tools/zapret2/check-web-backend.py <pinned-padavan-tree>
python tools/zapret2/verify-source-base.py
python tools/zapret2/verify-deps-base.py
```

These checks do not flash or reboot a router and do not establish device
runtime acceptance.
