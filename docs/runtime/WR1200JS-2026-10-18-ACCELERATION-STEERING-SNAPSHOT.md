# WR1200JS acceleration and Band Steering snapshot — 2026-10-18

Read-only SSH snapshot from `ASUS@192.168.20.1`; no service, setting, radio,
tunnel, or router state was changed. Device clock: Oct 18 18:19:43 EETDST.

## Device and resources

- Product: WR1200JS; kernel: Linux 4.4.198. `buildno`/`extendno` did not return
  a firmware identity in this shell snapshot. The WebUI screenshot from this
  session showed `4.4.198.9-474_4fc90055`.
- Uptime: 2,739.93 seconds (about 45 minutes 40 seconds).
- RAM: 123,652 kB total; 57,140 kB available.
- ZRAM: `/proc/swaps` shows active `/dev/zram0`, 30,912 kB, 0 used; total/free
  swap both 30,912 kB. This is active swap, not merely an enabled setting.
- Stubby: enabled, process running; DoH setting is off and no DoH proxy PID was
  returned. See the separate [DoT check](WR1200JS-2026-10-18-DOT-CHECK.md) for
  listener, strict TLS configuration, upstream sockets and DNS response.
- WireGuard utility listed interface `wg1`; no tunnel keys or peer configuration
  were collected.

## WAN/LAN hardware acceleration

- `hw_nat_mode=2`; kernel module `hw_nat` was loaded (`67440` bytes reported by
  `lsmod`).
- Current kernel log contains HNAT start, stop, then start. The latest syslog
  HNAT status line at 18:09:22 says: `Enabled module, requested offload
  [WAN]<->[LAN]`.
- Both Wi-Fi interfaces `ra0` and `rai0` were `UP`/`LOWER_UP`; wireless driver
  modules `mt76x2_ap` and `mt76x3_ap` were loaded. The firmware build policy
  disables Wi-Fi HNAT registration, so mode 2 requests the wired WAN↔LAN path.
- The retained kernel ring contained 33 `mtk_pong_hqos_handler:drop` entries at
  collection time, including `rai0`. These messages alone do not establish
  packet loss, a driver fault, or whether HNAT accelerated a particular flow.

**Assessment:** HNAT is configured for wired WAN↔LAN and its module is loaded;
the router logged that requested mode. A measured data-path acceleration or
throughput comparison was not performed, so end-to-end acceleration is not yet
accepted as proven.

## Band Steering

- `wr_bs_enable=1`; cached `wr_bs_apply_state=5` and
  `wr_bs_off_confirmed=0`.
- Daemon PID 951 was present. `/var/run/wr-band-steering/control` existed with
  owner-only socket permissions, and `/usr/sbin/wr-band-steering-ctl status`
  returned `active`.
- Both radio interfaces were up and their driver modules loaded. The daemon's
  active status is a live service observation; no client roam/steering event was
  exercised or observed in this snapshot.

**Assessment:** Band Steering daemon/control currently reports active, unlike
the earlier read in [the first runtime report](../evidence/WR1200JS-BAND-STEERING-RUNTIME-2026-10-18.md).
The earlier missing-process observation is historical and superseded by this
later snapshot. Client steering behavior remains unverified.

## Follow-up evidence needed

1. Compare WAN↔wired-LAN transfer throughput with offload enabled/disabled and
   check counters before/after; preserve remote access and do not change the
   mode without a safe recovery path.
2. Observe a known Wi-Fi client and fresh Band Steering events/status while it
   changes signal/band. Do not infer successful roaming just from `active`.
3. Investigate the repeated HNAT `drop` messages against source/driver semantics
   before treating them as faults or ignoring them.

This report is a sanitized operational summary, not a complete raw device dump;
public WAN addresses, client MACs, VPN keys, and full logs were not saved.
