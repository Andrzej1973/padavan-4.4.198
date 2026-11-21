## Existing retained owner candidates — 2026-11-21

rc-backend.c retains backend and rebind owners at stable private addresses.
wr_iot_rc_rebind_active_current validates request ID/time, adapter epoch,
device generation, physical nonce/serial and all six request fields against
rebind.start.input, then requires the actual rebind observer. This is an existing
provenance route to reuse rather than introducing global saved credentials.
wr_iot_rc_config_backend_capture/current already binds save/edit ownership to
a current backend kind/ID/time and refuses radio-owned transitions. It captures
backend identity, not a transferable credential or permission to mutate radio.

The driver owner is a different lifetime: driver-api-owner.h owner_take borrows
the request only until synchronous leave; leave wipes credentials. A later OFF
observer must not retain that pointer or infer its validity from a matching WCID.
OPEN's loaded-key admission and persistent driver generation readback must be
joined to the retained RC generation at the existing handoff. Physical main
radio OFF includes INITIAL/cold/disabled paths without an ACTIVE runner, so
an ACTIVE-only accessor cannot replace every off_profile_current call.

Implementation must first define those separate origin cases at radio-off
admission/profile generation/followup and radio-on admission; do not turn a
missing ACTIVE owner into legacy fallback for a present desired generation.
This refinement leaves the source mismatch unresolved and keeps promotion false.

## Concrete remaining OFF provenance gap — 2026-11-21

Source trace: radio-on-generation.c captures config_revision/provisioning and
binds that pin around generation. Its profile-current observer uses the captured
provisioning through restart_profile_file_current when the desired record was
present. radio-on-release.c calls that observer, retaining separation from later
desired writes. This establishes source intent, not loaded hardware acceptance.

By contrast radio-off-profile-check.c:wr_iot_rc_off_profile_current reads
precreated-profile-request.h, whose source keys remain wr_iot_ssid/wr_iot_psk,
and calls restart_profile_current. radio-on-admission.c, radio-off-profile.c and
radio-off-followup.c use that check. A newly generated desired profile can differ
from those legacy credentials, so the old observer can refuse that legitimate
generation. This is a source-derived mismatch risk; no device failure is claimed.

Required implementation: retain private loaded-generation provenance through
successful generation/OPEN handoff, including ownership and exact generation,
BSS/profile identity and observed loaded credential evidence. Route OFF/reopen
validation through that retained identity; do not recapture current desired data
or replace legacy keys on save. Admission must refuse missing/foreign/stale proof,
retain uncertain ownership and preserve old-generation shutdown after a later
save. Define promotion/retirement at actual lifecycle boundaries before binding
this observer. A generated-file match alone cannot certify loaded PMK.

Cover desired A generated/loaded, desired B saved while A remains active, OFF of
A, subsequent B generation, stale receipt/reused generation, PID/context copies,
Main/Guest preservation, failed OPEN and uncertain CLOSE. Existing generation
owners and driver admission should supply the chain; do not add a parallel global
credential cache. Keep configuration_loaded_promotion_bound=false until source,
target and image integration provide the required evidence.

## Current integration checkpoint — 2026-11-21

Hybrid Modern settings/apply resumed by the owner on2026-11-20; IoT remains
first. Older pause/unpublished/next-step statements below are historical.
Do not infer current absence of an implementation from those statements.

Source recheck on main14ef311c finds saved-config-store.c, config-save-server.c,
flash-save-native.c and native-flash-reader.c. The save facade registers only
when both native readback and snapshot capabilities are verified. Native save
uses the checked WR_NVRAM_IOCTL_SAVE_PROFILE path outside PID1; it is not an
unconditional HTTP NVRAM write. prepare-runtime.py stages save/edit/view startup
and reports HTTP route binding separately. Those sources do not by themselves
prove durability, loaded-profile promotion or main-image installation.

The runtime report still explicitly sets configuration_flash_bound=false and
configuration_loaded_promotion_bound=false; package-candidate-pair.py requires
both false. Do not flip these fields to claim completion. Next trace the actual
edit-view HTTP → typed mailbox → RC edit owner → store/save → fresh observation
chain and its loaded-generation handoff. Reconcile implemented pieces before
adding another facade. Verify native writer arbitration, KEEP/REPLACE revision,
manual/automatic save outcomes and retained old-generation shutdown identity.
Only then change the manifest contract with source, target and image evidence.
Optional1451 proves prepared FT TUs, not this configuration acceptance.
No router state changes are authorized.

# WR1200JS desired configuration and generation provenance

Current source package, 2026-11-17. Experimental candidate only. Source/host
verification is not a target image or physical device acceptance. Modern paused.

## Separate authorities

* `wr_iot_config_v1` is complete desired provisioning, including credentials and
  subnet while OFF. Runtime OFF remains an empty request.
* A generation owner captures a canonical revision (or proven absence) under the
  actual service guard. The pin binds PID, stable address, nonce/serial and
  transaction. Unknown/malformed input refuses; absence alone permits legacy
  policy. Factory entropy remains boot-only.
* Generated-file proof compares captured credentials, strict third-BSS fields,
  independent file reads and inode/stat identity. It is not loaded-PMK proof.
* Driver OPEN separately checks requested SSID/PMK before mutation under the
  task-owned BSS ticket. ACTIVE uses retained runner input, expected temporary
  snapshot, network/services/filter and fresh epoch/generation/OPEN token.
* RAM receipt is not flash durability. Native GET/GETALL read cache only.

## Implemented source paths

`saved-config-store.c/h` implement coherent complete capture and immutable
revision observation. A synchronous shared generation view borrows one pin;
nested binding, copied contexts, wrong PID/leave and releasing a borrowed pin
refuse. The view rechecks native state, decodes pinned credentials and wipes
private temporaries. Invalid bound view never falls back to legacy/entropy.

`rc-mode.c` takes two agreeing complete captures under verified native snapshot
capability, checks mode again and selects complete ON or empty runtime OFF.
It leaves outputs unchanged on error. Capability0 preserves existing legacy
behavior. Candidate preparation verifies the actual native dump/generator/header
and capacity before enabling1.

`cold-on-generation.c` binds the revision to initial DOWN admission nonce and
Main-close serial. `restart-generation.c` binds INITIAL/CLOSE post-RELEASE origin
nonce and serial. `radio-on-generation.c` binds the retained OFF release receipt.
Each retains existing physical/file/guard checks, requires agreement with the
supplied request and exposes the pinned profile only during its one generator
callback. Desired drift/read error before Main causes owned file restoration,
never another generator call. Reload0 still requires a matching existing profile.

`prepare-rc.py` installs generation-profile.h and a weak unbound selector into
ralink.c; candidate store provides the strong implementation. The actual native
2G generator supports disable_autoscan0/1. The RC wrapper now forwards either
exactly and refuses other values. Vendor1 selects channel1 when automatic2G
channel0 was requested, with AutoChannelSelect0; ordinary0 is unchanged.

After possible Main startup, captured generated-file provenance stays separate
from later desired changes. `radio-on-release.c` uses that generation observer
rather than re-reading legacy desired keys. Existing `rc-cold-start.inc` copies
the request into the retained backend and ties driver identity to the parent.
Parent cleanup occurs only after independent backend/shutdown-route preflight.
Cold cleanup wipes the entire generation; post-RELEASE rollback and ON release/
shutdown explicitly clear the new revision and provisioning buffers.

Legacy restart/OFF readers are not globally redirected to live desired data.
Doing so would invalidate an active owner's old-key shutdown identity after save.
No MCU protocol, ACK reuse, shared TX queue, DMA ownership or radio timing change.

## Verification

Host tests exercise actual native capture/store/snapshot parsing and real file
journals with explicit native/SDK/guard/driver boundary actors:

* canonical complete OFF data, absence/error/malformed and concurrent replacement;
* PID/address/transaction ownership, no SET replay and borrowed-pin lifetime;
* initial, post-RELEASE and OFF-to-ON new ON/OFF credentials, mismatch refusal,
  drift/error restoration and no repeated generation;
* retained generated-file proof after desired change, foreign-file refusal;
* full ON owner/mode/release/WAN/terminal with absent and configured records,
  old legacy SSID retained, terminal private credential wipe;
* actual producer fragments through ABI extractor in original/coordinated modes;
  actual weak default plus strong provider link; strict private selector refusal;
* prepared0/1 isolated staged syntax and early header closure;
* actual extracted RC adapter forwards0/1 and exact result, refuses other inputs.

General host preflight passed71 standalone cases plus its focused compositions.
The existing218-case lifecycle suffix passed. It is not the full287-case suite.
Source changes made during that run (ON integration, terminal wipe and adapter)
were checked by focused actual compositions afterward; do not present the older
run as proof of every byte of final source. See the package evidence for exact
hashes and verification scope. Target/link/image/device checks remain required.

## Remaining delivery

Complete target build and independent image/DSO verification, then validate all
loaded-owner handoffs and ordinary toggles without physical restart/scan under
explicit device authorization. Retain exact source/build/runtime boundaries.

Implement native manual/automatic flash-save outside PID1 without changing
existing policy. Automatic nvram_commit_safe is void and skips manual mode;
manual CommitFlash aggregates syscall result. Kernel COMMIT snapshots cache
before the flash mutex and early-major can return0 without writing. Durable
per-profile acknowledgment needs serialized revision and authoritative persistent
readback; RAM GET or bare zero return alone cannot prove it. No flash writer or
new durable status is implemented in this package.

Classic configuration/read/keep-password integration, main-image promotion,
physical acceptance and the final four Hybrid Modern/Classic/CAKE variants remain
separate requirements. Mi Mini follows WR1200JS acceptance.
