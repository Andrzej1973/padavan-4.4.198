# IoT OFF captured-owner correction

Scope: staged RC activation controller only; no production backend binding,
firmware protocol, ACK reuse or RF retirement changes. Root cause is a logical
owner handoff hazard, not a demonstrated device disconnection cause.

Previously stop captured only generation, called LOCK through state->backend,
then on stale admission unlocked through state->backend/state->context again.
If a successor context/backend was published during acquisition, that release
addressed the successor rather than the actual acquired owner. Existing
post-lock generation checks prevented subsequent teardown but not wrong unlock.

Regression publishes a successor from the existing LOCK callback model (no
unsynchronized parallel C access). Initial code aborts at unlock's f->locked
assertion. Fix captures backend/context before acquisition, validates callback
pointers, acquires via captured pair and always releases that pair on rejection.
Post-lock identity must match as well as generation/state. Already completed OFF
returns success only for the same captured owner; a different inactive owner is
not accepted. Caller still pins both objects through lock acquisition/release
and serializes state access; this does not create thread safety or refcounts.

Six cases cover context/backend/both replacement, backend replacement without
generation change, same-owner already-inactive completion and different inactive
owner refusal. Original activation failure/cancellation/recovery cases and
precreated100 cycles,11 start-stage/10 stop-stage persistent failures pass with
GCC warnings-as-errors and ASan/UBSan. Successor unlock count and teardown state
remain unchanged; original owner is released once. No radio/profile fallback.

Only host/injected backend acceptance: exact MIPS TU build pending. Existing ABI
workflow compiles check-activation.c for MIPS and runs both controller fixtures
in optional driver checks. The controller remains unbound; no safe late-TxS/
RF/DMA/IRQ release proof or firmware ACK ID reuse contract is supplied here.

Cleanup: baseline temp163808B, first corrected fixtures362632B and final extended
fixtures395272B removed by owned TemporaryDirectory scopes. Final absence check
passed; no core/core.* file present in checkout. Core dumps explicitly disabled
for subsequent regression runs. No router operation or retained build tree.
