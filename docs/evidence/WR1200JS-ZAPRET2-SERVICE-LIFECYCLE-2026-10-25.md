# WR1200JS Zapret2 service lifecycle — 2026-10-25

## Scope

Commit `c31a96d` adds the packaged `/usr/sbin/zapret2` lifecycle entrypoint and
a host-side lifecycle test. It does not enable or start the service, flash the
router, or establish device runtime acceptance.

The WR1200JS kernel configuration already contains:

```text
CONFIG_NETFILTER_NETLINK_QUEUE=y
CONFIG_NETFILTER_XT_TARGET_NFQUEUE=y
```

## Implemented behavior

- `start` requires an executable `nfqws2`, a non-empty root-managed strategy
  file and a valid WAN interface name.
- NFQUEUE rules use queue 200 and `--queue-bypass`, so closed or missing
  userspace queue handling does not intentionally hold traffic indefinitely.
- The dedicated `ZAPRET2` chain returns private and loopback destinations before
  the TCP/UDP queue rules and is hooked into `mangle POSTROUTING` for the
  configured WAN only.
- No `LOG` rule or daemon output is installed, preventing log flooding.
- Process ownership is checked against the exact configured `nfqws2` path in
  `/proc/<pid>/cmdline`; a stale or unrelated PID is not killed.
- `start` reconciles a singleton process and complete rule chain. `stop` removes
  the hook and chain and confirms process absence. `status` reports process and
  rules separately.
- Package staging copies the service as `/usr/sbin/zapret2`; the exact-image
  service map now requires both `/usr/sbin/nfqws2` and `/usr/sbin/zapret2`.

## Verification

Host command:

```text
sh tools/zapret2/test-service.sh
```

Result:

```text
PASS Zapret2 host lifecycle checks
```

Covered cases:

- shell syntax;
- first start and idempotent second start;
- independent process/rule status;
- detection and repair of missing NFQUEUE rules;
- stop and complete chain removal;
- stale PID cleanup without killing an unrelated process;
- refusal of an empty strategy file or unavailable WAN;
- presence of `--queue-bypass` and absence of a `LOG` rule.

`python tools/zapret2/verify-source-base.py` still passes for 253 files and
2,516,830 bytes at upstream commit
`4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`.
`python tools/zapret2/verify-deps-base.py` passes for all three pinned archives.

## Remaining gates

- A firmware build must verify `/usr/sbin/zapret2` and target BusyBox syntax in
  the final ROMFS.
- The strategy file, update policy and WebUI control are not implemented yet.
- No firewall rules were loaded on the physical router.
- No routing, blocking effectiveness, sustained traffic, reboot persistence or
  management-access test has been performed on the device.

Status: **implemented, host-tested; final-image and runtime verification
pending**.
