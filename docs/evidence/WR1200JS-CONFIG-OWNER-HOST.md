# Task-pinned bootstrap configuration ownership — 2026-11-06

The isolated config-owner layer stages begin/finish operations without calling
them from init or opening normal command/data admission. Begin requires the
current owned context, firmware receipt, completed scheduler and hardware actor
states, frozen constructors, drained messages/sender and safe ledger/device
state. It pins current with get_task_struct before publishing the owner under
transition → sender locks. Failed begin drops that temporary reference outside
locks. Explicit linux/sched.h is included in the existing guarded core region.

Finish recognizes only the original task plus historical exact ticket. Foreign
or stale callers leave ownership and its task reference intact. A legitimate
finish records software completion or retained failure, clears the task field
and drops its reference outside locks. Constructors stay frozen and normal
admission stays closed. A task reference prevents identity reuse; it does not
pin adapter lifetime, which remains the caller's responsibility.

Fresh generated-source ASan/UBSan fixture passed: success, duplicate begin/end,
foreign task and ticket, peer loss, hardware/messages failure, explicit failure,
missing/stale firmware/scheduler receipts, quarantine, clock and suspend. Task
reference operations and locks/context are injected, not real kernel threads.
Complete generated-tree SHA inventory matches the manifest. Temporary candidate
(~14MB) and executables were automatically removed. The peer82 recipe now stages
the layer/test; kernel API compatibility and target compilation remain pending.

This is an unbound prerequisite. It does not yet admit any configuration command
or validate hardware after configuration. Wiring must handle ACK and no-response
commands distinctly, retain failure, guarantee finish/abandoned-owner cleanup,
preserve adapter lifetime and support fresh checked epochs for repeated opens.
Neither task ownership nor state2 is a grant to publish normal data readiness.
