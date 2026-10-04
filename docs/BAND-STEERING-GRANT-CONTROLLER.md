# Correlated Band Steering grant controller candidate

`grants.c` is an isolated userspace controller, not an installed router service. It deduplicates pending operations per client/radio, queries record presence before adding, and requires a second query after an absent record is added. Ioctl success never marks a grant confirmed. An already-present record is not redundantly added; this avoids the modern CLI_ADD reset-to-INIT side effect in ordinary grant synchronization.

Replies must match radio, MAC, userspace slot, nonreused cookie, client identity/birth, activity generation and a 3-second deadline. A post-add absent result, index error, timeout, cookie exhaustion or send failure is fatal to the controller. Its future owner must stop/disable the steering session on failure. Record presence is refreshed every 5 seconds when sync is called. Confirmed means a matching steering record was observed; it does not prove association or future persistence.

A client observation in the same millisecond advances the activity generation and invalidates an outstanding proof. Idle-aging absence and legacy driver deletion require explicit invalidation before resync; dirty records are excluded from the confirmed mask. Desired-mask withdrawal cancels pending creation, and this controller sends no delete/deauth commands. Existing records are left to the separate non-deauth idle proof or an actual driver deletion event.

Integration contract: single non-reentrant event-loop owner in an ACTIVE driver session, prepared readback handlers on both radios, fresh/drained listener on init, no grant synchronization for a slot while its idle proof is active, and client slots recycled only after dual-radio absence. Controller and aging cookies are interpreted through distinct reply action types; neither controller may reuse its own cookies within the process instance.

The persistent coordinator must enforce those contracts, propagate errors to session shutdown, and deliver modern auth-request events after client observation. The module now marks those events for readback and repairs an entry only when the reply also reports modern ASSOC state. It requires a second readback proving that the blocking ASSOC state is no longer present, otherwise the controller fails. Ordinary ASSOC readbacks without auth intent never trigger CLI_ADD. Profile/start-stop wiring, WebUI and full vendor-driver compilation remain pending. Router runtime verification remains pending.

The isolated workflow runs ASan/UBSan fixtures covering query/add/readback order, pending deduplication, identity/generation checks, refresh, dirty-record invalidation, timeout/send failure and failed post-add proof, then cross-compiles grants.c for MIPS.

## Reauthentication verification scope

Fixtures cover modern ASSOC state without auth (no reset), auth with an already non-ASSOC record (no reset), auth plus ASSOC (one reset followed by readback), and a failed reset whose readback remains ASSOC (controller failure). Driver-case fixtures use the enum extracted from the pinned prepared header. This is isolated source/fixture evidence; full vendor-driver compilation, persistent coordinator integration and actual router reconnect tests remain required.
