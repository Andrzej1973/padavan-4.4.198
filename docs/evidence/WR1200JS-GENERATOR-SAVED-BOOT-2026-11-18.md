# Initial IoT generator selection from saved configuration

## Source gap

The isolated RC candidate can save a complete desired IoT record and
`wr_iot_rc_radio_on_saved_request()` selects that record for boot/runtime
requests. However, initial profile generation calls
`wr_iot_generation_boot_request_read()`. Previously its strong selector returned
0 whenever there was no synchronous generation override. That selected legacy
`wr_iot_enable/ssid/psk` keys (or factory credentials), even when the new complete
record existed. Loaded and desired credentials could therefore differ after
boot. Existing loaded-profile checks should refuse that mismatch; bypassing
them would not solve configuration integration.

## Correction and ownership

`saved-config-store.c:wr_iot_generation_profile_request()` now uses the existing
native snapshot reader under the existing nonblocking service guard when no
admitted generation view is bound. Two complete captures must agree in presence
and decoded contents. It returns a provisioned profile for both desired ON and
configured OFF, retaining SSID/security for a disabled reserved BSS. It does not
write legacy keys, new configuration, runtime gates or flash.

Only proven absence returns 0 and permits the old legacy/factory policy.
Malformed records, snapshot/ENOSPC errors, lock contention and observed drift
return -1 without modifying the output. The generator then does not reserve
ra2; it does not create an open fallback network. Unprepared source builds retain
their previous weak/legacy policy. A bound admitted view retains its existing
PID/address/revision checks and takes precedence over the boot selection.

The borrowed service guard depth is released on all paths. Captured records
and temporary keys are wiped. This is a synchronous snapshot, not a lease over
the whole generated profile or proof of hardware loading. A later desired
change must still pass existing loaded-profile and activation ownership checks.
No restart/scan, ACK reuse, DMA completion or radio timing behavior is added.

## Verification scope

Focused host checks passed for the actual selector with native store, snapshot
parser and service guard: configured ON/OFF, proven-absence legacy fallback,
malformed/error/drift refusal, no writes and nested guard preservation.
The fixture also exercises a fork contending with its parent's real guard.
Existing saved-store prepared0/1, RC desired selection, literal generator
original/coordinated modes, ON generation/owner, cold configuration revision,
restart desired configuration and generated-unit staging checks passed.

The complete edit/view suite includes the new initial-generation test and
completed with exit0 before publication. Host checks use external NVRAM and
SDK actors and do not establish MIPS compilation or driver/runtime acceptance.
Exact-source optional link/image verification remains required. Keep
`configuration_loaded_promotion_bound` and production acceptance gates false
until their full integration evidence is available.
