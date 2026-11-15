# ON shutdown after Main UP, before ra2 handoff

The standalone `radio-on-prehandoff.c` observer checks the new ON parent directly,
without constructing a restart-origin object. It requires pending normal
shutdown, stable owner/children, generation VERIFIED, possible submitted Main UP,
no handoff timestamp, owned profile baseline/current desired profile, Guest DOWN
(or policy OFF), fresh rebind configuration observation and exact new epoch/same
device generation. The retained original OFF receipt is independently checked by
the ON generation origin adapter. Guest recovery uses its existing one-shot
DOWN path. Neither that administrative DOWN nor this witness proves physical
RF/DMA/IRQ retirement. No profile restoration after UP is granted.

The source audit confirms existing RC quiesce_shutdown_begin/advance and
rc_rebind_shutdown_closed cover the later ACTIVE-to-CLOSED handoff case. They
must retain exact ON ID/time, original RELEASE, new Main identity and the newly
completed OFF owner; a rejected-before-OPEN path has a separate witness. Existing
restart physical cancellation functions own a different static physical context
and must not be called with synthetic restart objects for the new ON root.

Host C11-Werror ASan/UBSan actual restore composition passes Guest UP refusal,
one Guest DOWN on pending shutdown, fresh positive proof, old epoch, wrong device
generation, stale receipt, NOT_SUBMITTED Main and post-handoff refusal. Baseline
and guards remain held. SDK/identity boundaries are injected. The observer is now registered and staged for experimental target compilation
after the earlier full host suite completed with observed exit0. Root cleanup
binding is still pending. Next bind this proof to bounded root cleanup
for stock shutdown, then implement exact post-handoff CLOSE/rejection handling.
No target, image or physical runtime acceptance is claimed. Fixture scratch was
removed by TemporaryDirectory.

## Child-drain and profile-phase preflight

The witness explicitly refuses busy Guest/service/multicast children, any WAN
or terminal-IAPP ownership/attempt, and every Main phase except submitted WAIT
or observed READY. It also rejects profile recovery/removal/restored state and
checks generated/sealed versus no-reload journal invariants. These are required
before cleanup is considered: a matching Main alone cannot release a parent
with an in-flight child. The expanded host fixture independently corrupts each
predicate and confirms retained ownership with no extra UP/DOWN submission.
The root cleanup binding remains deferred until the live full suite terminates;
its registered sources are unchanged during execution.

The service and multicast children must also belong to this process and point
to this exact parent's Guest/Main objects whenever they have an owner. Zero
busy flags alone do not establish that relationship. The host fixture rejects
foreign PIDs and each detached parent pointer independently; a valid chain
continues to pass without any additional mutation.

## Post-handoff witnesses

`radio-on-shutdown-check.c` validates ON-specific HANDOFF, exact creation time,
new Main identity and old physical RELEASE through existing strong backend
witnesses. A newly owned OFF must be terminal CLOSED; pre-OPEN rejection uses
its separate no-OPEN/no-resource witness and is never mislabeled CLOSED.
Guest must be DOWN and parent origin still current. Neither case restores the
obsolete startup profile. The host fixture uses actual ON restore/handoff/Guest
recovery with a backend boundary actor and rejects pending/state/epoch/receipt
mismatches. Prepared separate C11-Werror units pass; MIPS and real backend
composition remain separate. Both observers are included in ABI/target symbol
gates, with no public shutdown cleanup binding yet.

The full registered recovery suite958b5560 completed with observed exit0. Its
log hash/result and coverage boundary were saved; completed exact scratch
(42,172 bytes) was removed. New witnesses have separate focused evidence and
are not retroactively included in that full-suite result.
