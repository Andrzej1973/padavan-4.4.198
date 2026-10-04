# Band Steering client aging candidate

This module is an isolated userspace candidate, not an installed firmware service.

After at least 60 seconds without observed client activity, `aging.c` asks both driver interfaces whether the same MAC is absent. A single 3-second transaction requires two matching absent replies. Each radio gets a unique nonzero cookie; cookies are never reused within an initialized aging object and exhaustion fails closed. The slot, MAC, activity generation, reply deadline and radio must agree. Any intervening activity, including activity in the same millisecond, prevents freeing the client record. Present/error replies, partial send failure and timeout retain the client.

Only idle-query commands are sent. The modern radio requires the prepared safe-idle handler; using original CLI_DEL would disconnect clients and is prohibited for aging. The legacy AGING protocol already supplies a MAC-table presence check. This does not solve kernel association races: a client can appear immediately after the driver's presence check. No deauth is introduced by the new handler, but a steering record may be removed during that race. Consequently every absent reply, including a late or stale one, marks the current matching MAC's radio record as needing policy synchronization. The future policy must reconcile this flag before assuming an existing grant. New activity prevents userspace record deletion.

Integration prerequisites: one non-reentrant event-loop owner, ACTIVE driver session, driver table indices matching userspace slots, safe modern extension compiled, monotonic millisecond timestamps, and a fresh/drained listener before a new aging object starts. The module does not itself install a daemon, enable steering, reconcile grants or modify WebUI defaults. Those tasks and full driver/device verification remain pending.

The isolated ABI workflow compiles host fixtures with ASan/UBSan and produces a MIPS aging object. Fixtures cover two-radio confirmation, duplicate/stale/mismatched replies, slot reuse, same-time activity, presence/error, timeout, send failure and cookie exhaustion. Passing those checks does not establish actual device behavior.
