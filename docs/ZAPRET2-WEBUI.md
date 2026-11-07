# Zapret2 WebUI contract

## Current implementation

Zapret2 is controlled from **Administration → Services** in Padavan Classic.
The build-time selector remains `CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y`, while the
saved runtime switch is `zapret2_enable` and defaults to `0`.

The service page provides:

- a factory-off enable toggle;
- a bounded textarea for `/etc/storage/zapret2.args`;
- Apply-triggered `stop`/`start` reconciliation;
- a separate observed-status panel for process, NFQUEUE rules and strategy;
- EN, UK and RU labels.

The strategy editor accepts arguments for `nfqws2`, not shell commands. The
service supplies queue number 200 and the three pinned Lua initialization files.
An enabled switch with an empty strategy is rejected by the page and by the
service itself. Both layers enforce an 8192-byte maximum.

## Safety properties

- The web request only changes NVRAM and the root-managed strategy file through
  the existing Padavan form/event path.
- Apply reuses Padavan's existing firewall event so no HTTP event bit is
  consumed; the firewall reapply hook then reconciles Zapret2.
- `restart_zapret2` stops the owned process, removes the dedicated rules and
  starts again only when the saved switch is `1`.
- general firewall, netfilter and WAN-firewall restart paths reapply Zapret2
  after Padavan rebuilds its rule tables.
- NFQUEUE uses `--queue-bypass`; no `LOG` rule is installed.
- The chain is attached only to `mangle POSTROUTING` for the configured WAN and
  returns LAN/loopback destinations before queueing.
- Status reads process presence, the strategy file and the WAN-specific NFQUEUE
  hook separately. It does not claim that bypassing, routing or WAN health is
  working.

## Verification levels

- Source transform: prepared against pinned Padavan commit
  `c25283e915a2a00a763774dd255b14aff997285e`.
- Host tests: emitted browser script syntax, service lifecycle, strategy
  requirement and NVRAM/event wiring.
- Final image: must contain the page controls, compiled HTTP status/restart
  routes, three dictionaries, `nfqws2`, service, Lua files and license.
- Runtime: not verified. The router has not been flashed or rebooted, and no
  strategy has been run on the device.

The status label “process, strategy and rules present” is not proof of successful
blocking bypass or preserved management access. Those require a separately
authorized device test with a local or VPN recovery path.
