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
and guards remain held. SDK/identity boundaries are injected. The observer is
not yet registered/staged/bound: the earlier full host suite is live, so its
registered inputs were preserved. Next bind this proof to bounded root cleanup
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
