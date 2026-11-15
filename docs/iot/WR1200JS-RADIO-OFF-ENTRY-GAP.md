# Physical radio OFF entry integration gap — 2026-11-15

Scope: source audit of 6c786921; no device action or acceptance.

The existing private restart entry accepts radio_on=1 only. Extending it to
radio_on=0 is not a one-line predicate change.

| Boundary | Current source | Required work |
| --- | --- | --- |
| Intent | restart-entry.c initializes {restart=1,radio_on=1,reload} | Define OFF intent and SDK side effects separately from ON resume |
| Physical progress | rc-physical-stop.c stops polling after result is published | Install an explicit process-owned terminal consumer; otherwise owner remains allocated |
| Consumption | wr_iot_rc_physical_take clears the retained context exactly once | Consume only the matching private OFF transaction, never another caller's result |
| Scheduler | restart-scheduler.c requires restart && radio_on | OFF cannot be handed to the existing ON scheduler |
| Signal replay | non-restart physical_step ends fence before assigning physical.result | Before enabling OFF entry, test pending shutdown and prove cleanup/publication ordering; do not infer it from ON resume cleanup |
| Legacy fallback | prepare-rc.py calls wr_iot_quiesce before stop_8021x/profile generation; rc-backend.c refuses ACTIVE/STOP/OFF | Preserve refusal and isolation; a failed private entry must not bypass it |

Implementation acceptance: a private OFF owner with exact intent correlation;
nonblocking completion through RC wait; one terminal take; no ON scheduler,
profile regeneration or accidental reopen; pending SIGTERM/SIGQUIT, failed mask
restore, repeated OFF, new ON after completed OFF, and foreign-result refusal.
Existing saved configuration must survive. Inspect the pinned SDK OFF branch
for required LED/auth/IAPP/WAN behavior before selecting those side effects.

The current full host suite remains separate evidence. Its success cannot
prove this not-yet-bound OFF entry. The radio_on=0 refusal remains in place.
