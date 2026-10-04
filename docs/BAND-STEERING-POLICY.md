# Band Steering preconnection policy candidate

The policy module is an isolated decision engine. It is not installed in firmware and performs no driver I/O. The persistent controller, actual grant verification, profile/service integration and WebUI remain pending.

The fixture configuration prefers a freshly observed 5 GHz RSSI of at least -70 dBm, holds a new 2.4 GHz request for at most 1.5 seconds when no strong 5 GHz observation exists, and permits 2.4 GHz fallback after 3 seconds even when 5 GHz looks strong. Only-5 GHz observations with unknown RSSI receive a 3-second fallback too. The policy preserves existing verified grants rather than disconnecting clients to force a band change. These are proposed policy parameters, not measured router performance settings.

The source legacy 5 GHz driver can remove a steering entry and kick a low-RSSI client through BndStrg_IsClientStay. A legacy CLI_DEL observation clears the controller's 5 GHz state and introduces a 30-second policy cooldown; during that interval 2.4 GHz is permitted. The decision engine does not blindly re-add the 5 GHz record on every subsequent probe. RSSI samples expire after 10 seconds in the fixture configuration. Slot identity/birth and MAC are tracked so recycled clients do not inherit cooldowns.

Idle-aging absence reports mark records needing reconciliation. The policy returns a reconciliation mask for desired records, including retained grants. The controller must not repeatedly send modern CLI_ADD: the driver resets an existing client's state to INIT on that command. It must deduplicate pending operations and verify whether a record exists, then reconcile once as needed. An ioctl success cannot be used as confirmed_mask: the current driver dispatchers can ignore handler results and there is no completed grant-readback integration yet. A desired mask reduction following a legacy kick acknowledges an already-removed grant; it does not authorize a new deauthentication/delete command.

Both drivers use table membership to accept selected connection requests in preconnection mode. The modern radio has additional WPS/whitelist/blacklist handling and special behavior for reauthentication of a previously associated entry. The grant controller now handles an auth request plus an ASSOC-state readback before requesting a reset and verifying its result. The future persistent coordinator must wire those events in the required order; this policy module alone does not establish reliable reconnect behavior.

The isolated workflow tests radio-index order, fresh/stale RSSI, bounded single-band fallback, retained grants, aging reconciliation, kick cooldown, slot reuse and invalid input using ASan/UBSan, and cross-compiles policy.c for MIPS. Actual full driver compilation and router runtime acceptance remain required.

## Reauthentication verification scope

Fixtures cover modern ASSOC state without auth (no reset), auth with an already non-ASSOC record (no reset), auth plus ASSOC (one reset followed by readback), and a failed reset whose readback remains ASSOC (controller failure). Driver-case fixtures use the enum extracted from the pinned prepared header. This is isolated source/fixture evidence; full vendor-driver compilation, persistent coordinator integration and actual router reconnect tests remain required.
