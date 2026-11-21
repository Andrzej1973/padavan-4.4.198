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

## Target result and missing feature coverage

ABI43004583856 for exact2beb63bf22c26c7957fbb7b06e0de231c6151497 succeeded.
Actual iot-activation-mips.o is ELF32LE MIPS ET_REL26968B SHA256
5baa2df07e9bf8baa7708599f3d57ed57d31de2a25fc239370cb17a6d97a2dad.
Its bytes include the new successor.unlocks==1 regression assertion. Exact
Git source/header hashes match the working files; successful host activation
step and text log independently inspected. Object remains a test TU, not the
production RC link or physical RF/lifetime acceptance. Companion TARGET JSON.

Inspection exposed a precise CI gap: this ABI step did not compile/run the
separate check-precreated-activation.c fixture, although the firmware optional
host loop did. Added host execution plus separate MIPS object to existing ABI
step, preserving concurrency, monitor coverage and all other checks. New
feature target result pending. Local identical -O2/ASan/UBSan host flags pass
100 cycles/all start-stop faults;299048B owned scratch removed, absence asserted.
No speculative CLOSE transport was added: opcode10 exists in staged codec/
entry but is not routed by the installed candidate ioctl dispatch. OPEN_CURRENT
or configuration CLOSED observations are not RF retirement/teardown permission.

## Separate precreated target fixture verified

ABI43006952508 for66a7ce810cf0246ae03cf21151c972fa4ca3a789 completed
success. Artifact13848169396 contains actual ELF32LE MIPS relocatable normal
and precreated fixture objects (26968B and35376B) and successful host reports.
Exact source/header/workflow bytes match Git. Companion
WR1200JS-IOT-PRECREATED-ABI-2026-11-11.json records hashes and test output.
This closes the test-coverage gap above. Production binding and physical
RF/DMA/TxS acceptance remain pending. No extracted scratch was retained.
