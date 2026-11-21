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
