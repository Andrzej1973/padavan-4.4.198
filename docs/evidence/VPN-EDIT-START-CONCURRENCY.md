# VPN edit/start concurrency audit

2026-10-18, source inspected at `b507b40`. Open correctness issue; no physical
router operation or demonstrated device failure.

`profilectl.c:wr_edit()` reads a record, validates it, calls `profile_state()`,
then writes with the record revision. `profile_state()` releases the runtime
operation lock before returning IDLE. `wr_up()` reads and validates a record,
resolves endpoints, then acquires its runtime lock and creates a session.

Possible interleaving: Up reads revision N; Edit observes no session; Edit
commits N+1; Up creates a session using its earlier N snapshot. Alternatively,
Up can create a session after Edit's idle check but before Edit's store write.
The expected revision check prevents competing record writes; it does not
serialize the entire idle-check/write sequence with link creation. Delete has
the same idle-check/write gap and must be included in the repair.

Next work: introduce a consistent mutation lock shared by profile edits,
deletion and activation, or hold the existing runtime lock through the record
change and revalidate the stored revision under that same lock before link
creation. Check lock ordering against store locks and nested apply operations;
preserve read-only operations. Add deterministic competing-process fixtures
covering both orderings, stale rejection and unchanged neighboring profiles.
Do not claim safe concurrent editing/activation until those checks pass.

Existing WG/AWG runtime acceptance, route/DNS behavior and management handover
still require physical-device verification with restored access and permission.

Repair candidate: `profilectl.c` now takes a private per-ID `.mutation-ID`
flock in the volatile runtime root before dispatching create/edit/delete/up/
down/apply, and retains it until the command returns. Existing store/runtime
locks are nested inside this outer lock, never the reverse. Read-only commands
remain unlocked, and different IDs have independent locks. Files are private,
single-link regular files opened with NOFOLLOW/CLOEXEC; lock files are retained
to prevent unlink/recreate splitting. No persistent profile format change.

Added host-manager and shipped-MIPS fixtures holding the actual lock from a
competing process: all five competing lifecycle/edit commands must return BUSY
before any network action, export must still work, and another ID must still
be creatable/deletable. CI execution is pending; deterministic scheduling of
the earlier internal idle-check window and physical acceptance remain open.
