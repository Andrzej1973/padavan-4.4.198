# WR1200JS test build 263 — StrongSwan deferred

[Run 38566074124](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38566074124), commit `5bf7330b8a5845c31e0e8700caf1abcf7481222f`, completed successfully. Downloaded artifact `WR1200JS_4.4.198.9-263_5bf7330b_TEST`, ID `11896592895`, is stored in the parent workspace's `build263-final` directory.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-263_5bf7330b.trx`: 12,578,554 bytes; `fce88e547afd44b5d309957e2f5390971c40adc6ba3b6a2c88ad0cacb7f82208`.
- `SETUP_WR1200JS.txt`: 22,986 bytes; `be4461e257c1eecd985fdeaaf6569e35297ed02b3aeddceb1bea805f3db5dc91`.
- `wr1200js.config`: 11,333 bytes; `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The downloaded profile matches the current requested profile byte for byte. StrongSwan is commented out; independent WireGuard/AmneziaWG, ZeroTier, DNS and XFRM selections remain. The packaged guide identifies build 263 and omits an enabled StrongSwan chapter. The main image step now rejects an enabled effective StrongSwan selector and the IPsec commands/private libraries when the requested selector is off; this step passed. The separate positive StrongSwan check is conditional and was not executed inside its successful shell step for this disabled profile.

Stubby and DoH image checks passed; the image Stubby DNS test under QEMU passed. These establish their specific build/packaging/emulated execution evidence, not physical router acceptance. This image has not been flashed by this work. Configuration retention, actual services/driver behavior, reboot persistence and sustained stability on this image remain open.
