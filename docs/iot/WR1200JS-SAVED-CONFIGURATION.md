# Saved IoT configuration and loaded profile

Implementation is in progress. The new saved-config.h codec and its strict-C11
ASan/UBSan fixture validate a complete SSID/key/subnet record even when disabled.
The codec performs no writes. The new saved-config-store.c implements a single
native SET under retained RC admission and the real service guard. Its snapshot
preparation capability defaults0, refusing before NVRAM reads/writes unless the
source preparer verifies the native overflow fix. No installed caller uses the
new record/store yet. Flash, HTTP/mailbox binding, migration, runtime ON and
radio generation integration remain unfinished. Existing runtime OFF is unchanged.

A single bounded versioned value is selected because native NVRAM SET replaces
one tuple under its kernel spinlock; it cannot atomically replace seven tuples.
Lowercase hex encodes all seven fields, preserving UTF-8 and delimiter bytes
without shell parsing. The maximum buffer is384 bytes, below the pinned native
NVRAM4096-byte value limit. This is an integrity/representation boundary, not
an authentication mechanism or a guarantee against later flash failures.

Three states must remain distinct:

| State | Authority | Required behavior |
| --- | --- | --- |
| Requested/saved provisioning | Complete versioned configuration | Retain credentials and valid subnet while OFF; use native manual/automatic flash-save policy |
| Currently loaded ra2 credentials | Existing driver generation and exact profile/PMK proof | A new saved preference must never impersonate the loaded key or invalidate the old safe-OFF owner |
| Runtime ON/OFF | Existing private mailbox/backend owner | OFF contains no new credentials; preserve saved provisioning and avoid physical restart/scan |

Existing restart-profile.c and radio-off-profile-check.c compare current saved
legacy SSID/key with the actual profile file. They are deliberately conservative.
Pointing those readers at a newly saved desired record while the old generation
is live would break their identity proof. The eventual store must therefore
retain old loaded-profile provenance until exact quiescence/retirement, and
promote desired configuration only through an explicitly owned provisioning
transition. Factory CSPRNG credentials remain boot-only and are not silently
persisted as a user's requested profile.

Next implementation steps: bind complete configuration to the existing operation
owner; add exact prior-record/readback and uncertain-write retention; preserve
legacy settings and factory absence distinctly from a malformed record; compose
loaded-profile identity across OFF/configuration change/new generation; integrate
native HTTP flash-save behavior without a PID1 flash writer; then activate the
Classic page with distinct queued/applied/save-pending/unknown states. Ordinary
runtime toggles must keep Main/Guest associations and never restart/scan radio.

Build/source/image and physical device acceptance remain separate. Modern WebUI
is paused. No router operations are authorized by this source work.

## RAM store verification — 2026-11-17

The private store binds PID, original context address, transaction ID/time and
retained service guard to one complete record. A fresh exact baseline is
required before SET. A possibly completed failing setter is never replayed;
later steps only reobserve. A read failure or foreign record holds the journal.
Cancellation needs the actual prior record; finish needs the actual desired
record. Both wipe/release only this store and leave outer shutdown admission
with the caller. Finish means RAM_READY, never flash durability or activation.
The dedicated key wr_iot_config_v1 is desired provisioning only; no legacy
saved/loaded key, temporary runtime gate or driver state is modified.

Actual store + actual service-guard.c + existing settings-snapshot.c passed
host GCC/Werror/ASan/UBSan with NVRAM syscall actors (session15124 exit0).
Cases include preparation capability0 refusal, absent/malformed/error reads,
no-op, one SET, pending TERM, PID/address ownership, error before/after mutation,
post-write read failure and foreign replacement before/after SET. No device
NVRAM or flash was accessed by these host tests.

The native library conflates missing/error in nvram_safe_get. Its whole-cache
reader provides an error status, and the already existing Band Steering
prepare-nvram-snapshot.py changes silent truncation into ENOSPC. The WR1200JS
config enables Band Steering and its source integration invokes that transform.
Installation of the new store must explicitly verify that transformed source,
its existing snapshot implementation and RC linkage before enabling capability1.
No new ioctl or kernel protocol is introduced. Keep installation disabled until
that source gate and the owning configuration operation are connected.

## Configuration operation owner — 2026-11-17

config-owner.c now wraps the RAM store in a distinct same-process RC operation.
It acquires one shutdown admission, captures the existing backend identity under
the service guard and initializes the nested store at its final address. It
never calls activation or uses the configuration transaction ID as an ON result.
The runtime backend remains the owner of the old loaded profile. ACTIVE requires
an already armed, available normal-shutdown route; the new configuration path
does not arm one as a side effect. Readiness captures are read-only.

A failed/uncertain store or changed backend retains the operation and its guards.
Explicit cancellation may release only the exact prior record. Terminal RAM
readiness remains owned until the caller publishes its exact outcome. Cleanup
then reobserves the backend/store, releases the nested/outer guards and ends its
own shutdown admission before delivering a pending signal. A private receipt
supports read-only current-record status after cleanup; it returns no credentials
and proves neither flash durability nor runtime activation. Retiring the receipt
wipes its expected configuration. A failed publication must retain the operation
and retry publication without calling begin or issuing SET again.

The actual config owner/store/backend passed the composed host fixture58406:
IDLE/ACTIVE/OFF identity, unarmed ACTIVE refusal, wrong address/transaction,
modeled publication delay, stale backend, fresh post-cleanup receipt, read error,
pending TERM and ordinary subsequent OFF. SDK resources, native syscalls and the
normal consumer are actors in that fixture; actual normal/physical composition
is a separate regression test. Six focused compatibility cases15851 also pass.
Direct additional cases13942 now verify INITIAL_OFF (including spent consumer
refusal), REBIND_ACTIVE and REBIND_OFF readiness against their actual retained
observers. Full configuration transport/new-generation flows remain untested.

There is no configuration CGI, mailbox/notification dispatch, RC wait-loop
continuation or IPC status route yet. Do not call this finished persistence or
activate a page. A distinct configuration outcome must not become runtime
APPLIED. The RC wait loop must retain/progress this exact configuration owner
and stop competing operations while it owns admission. Verify/publish terminal
configuration status before cleanup and retain its receipt for fresh IPC reads.
Next connect this transport/scheduling, then cold desired-to-loaded promotion
and native flash-save behavior. The store preparation capability still defaults0;
only the header required by the new read-only backend helpers was added to the
existing runtime source staging/check lists. Store/owner source is not installed.

Current source/host evidence: ../evidence/WR1200JS-CONFIG-OWNER-BACKEND-2026-11-17.json.
