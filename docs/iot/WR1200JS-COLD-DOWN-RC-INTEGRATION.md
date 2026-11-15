# Cold DOWN RC integration boundary

The cold path means ra2 was pre-created but never opened, while Main has a
completed close ticket. It is distinct from an IoT-owned physical RELEASE.
Fresh never-started Main is a separate case and is not covered by this proof.

## Implemented observation

`tools/iot/precreated-down-observe.c` requires active admission, a borrowed
configuration guard, saved initial-OFF policy, absent br-iot, BSS DOWN, no DNS
recovery and Main DOWN. Two typed driver reads must agree on adapter epoch,
ra2 generation and completed Main close serial. `wr_iot_initial_down_current`
repeats this observation and compares all three fields with a captured baseline.
Neither function changes driver state, generates a ticket or grants a future
reopen lease. The caller must retain its exclusion and object lifetime contract.

## Private cold admission implemented

`cold-on-admission.c` now captures a distinct typed DOWN baseline and the actual
read-only radio profile under the existing service guard and signal fence.
Historical RELEASE excludes this path. Repeated current checks surround profile
capture. A claimed refusal retains the fence/context until explicit cancellation;
cancellation frees capture only, preserves foreign file changes and runs before
pending shutdown replay. Failed signal-mask restoration retains ownership.
The component is staged for compilation but is not routed from public RC entry.

## Required integration, still incomplete

1. `radio-on-admission.c` currently requires `wr_iot_rc_radio_off_receipt` and
   stores a physical RELEASE. Cold admission must retain a distinct typed origin
   and fresh nonce under its own fence; it must refuse if historical ownership
   exists. Profile capture must be bounded by repeated current-DOWN checks.
2. `radio-on-generation.c` validates that same receipt before profile generation,
   rollback and Main UP. Cold provenance needs explicit checks before UP and
   separate rules after UP; a DOWN observer cannot succeed after Main UP.
3. `radio-on-main.c` and `radio-on-prehandoff.c` use
   `wr_iot_rebind_configuration_current`, comparing the new adapter epoch with
   RELEASE epoch. Cold startup needs an independently validated new Main READY
   and exact ra2 generation, without manufacturing CLOSE/RELEASE history.
4. `radio-on-handoff.c`, rebind-start/network/runner, shutdown checks and restore
   retain physical RELEASE identity. They need an explicit cold-origin path
   through success, pre-UP rollback, post-UP refusal and shutdown cleanup.
5. Only after those consumers are covered may `restart-entry.c` route cold ON
   into the new owner. Existing historical RELEASE routing must remain intact.

No generic weakening of RELEASE validation, native fallback after a claimed
cold admission, or use of DOWN snapshots as RF/DMA/IRQ drain evidence is valid.

## Verification

Actual observer and expected-identity revalidation pass host GCC Werror with
ASan/UBSan: changed epoch/generation/Main serial, zero fields, missing guard,
inactive or pending admission, policy/bridge/BSS/DNS/Main failure, first and
second transport-read failure. Prepared RC C11 objects compile. Full SDK target,
final image and physical WR1200JS acceptance remain separate outstanding gates.
