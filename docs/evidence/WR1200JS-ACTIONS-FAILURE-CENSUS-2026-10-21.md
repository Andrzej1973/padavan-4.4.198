# WR1200JS GitHub Actions failure census — 2026-10-21

## Scope and current result

Read all 960 retained Actions runs returned by the repository API (10 pages),
then inspected job summaries for every failed run categorized as a firmware
build or build-workflow definition. The snapshot ends at monitor run
`39646683016` (`#127`, skipped, 2026-10-21 17:45:52Z).

The 148 failed workflow runs in that snapshot split into 90 firmware build
runs, two failed workflow-definition runs (`#2` and `#198`, with no failed job
returned), 28 Band Steering driver ABI runs, 27 service-runtime runs, and one
Agent build failure monitor run. These are run counts, not 148 distinct source
defects. The monitor is not a firmware build.

Latest firmware run is [#514](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39644862386),
source commit `a6edff845ddbebd90e2833800445757290c921b9`; `select`,
`build-wr1200js`, `downloads`, and `firmware-zip` all succeeded. The latest
Band Steering ABI run, `39644862372` (`#489`), and service-runtime run,
`39616973001` (`#249`), also succeeded. The latest monitor run was skipped.
No firmware run newer than #514 appeared in the snapshot.

The latest non-passing runs in the other monitored workflows also have later
successful runs: ABI run [#458](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39155842539)
stopped on a source-parser assertion, then ABI #489 passed; service runtime
[#236](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39126754304)
stopped compiling a DNS process fixture because `wr_process_present` was used
but not defined, then runtime #249 passed. Monitor run
[#125](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39635018908)
failed while downloading Nim (`curl: (7) Couldn't connect to server`), before
it could inspect a build failure; this is an external setup/network failure,
not a firmware result. The newer monitor #127 was skipped as configured.

## Confirmed recent failure groups and closure

- #489 and #491: toolchain `nm` lookup; later #492 passed.
- #493: Lua shared-library fixture in the target BusyBox audit; later image
  audits passed.
- #494–#496: KVR fixture expected the wrong getter; #497 passed the preparation
  gate.
- #498: KVR options were absent from the effective build-tree config.
- #499–#500: MT76x3 WNM/PMF and FT/IGTK compile guards; #501–#504 passed.
- #505–#508: VPN pruning expected options already removed by the preceding
  VPN page transform; #509–#513 passed the corrected preparation step.
- #509–#511: QEMU dnsmasq failed to seed randomness while parsing the combined
  DNS configuration; the test was repaired to provide a guest `/dev/urandom`
  overlay; #512–#514 passed DNS checks.
- #479–#484: the final-ROMFS services navigation did not exactly match active
  build capabilities. #486–#488 passed afterward.
- #485: the Shadowsocks localization image checker joined the ROMFS root twice
  and looked for `trunk/romfs/trunk/romfs/www/Shadowsocks.asp`; #486–#488
  passed afterward.
- #512–#513: the Privoxy verifier failed to recognize the shared-Wi-Fi
  `validate_asp_apply(..., &shared)` form, although the Save failure branch,
  restart clears, error callback, and abort were present. The isolated matcher
  correction is commit `a6edff8`; #514 passed this final-image gate.

The run-by-run CI evidence for the #489–#513 sequence is in
`WR1200JS-BUILD514-RECOVERY-2026-10-21.md`,
`WR1200JS-BUILD513-SERVICE-AUDIT.md`,
`WR1200JS-BUILD506-507-VPN-HOOK-2026-10-21.md`,
`WR1200JS-BUILD505-FAILURE.md`, and the KVR/MT76x3 evidence files named there.
The failed downloads/index and missing diagnostic-artifact steps in those
runs were downstream consequences of the first failed image/build gate.

## Earlier development/test-build failures

The historical run inventory also contains repeated failures in earlier
`TEST` builds. Job summaries show repeated failure clusters at the SSH status
image verifier (#443–#447, #467, #469–#470), exact-target BusyBox audits
(including #334–#346 and #468), board-port preparation (#277, #431–#432,
#466), and a series of one-off image gates for IoT radio capacity (#449–#450),
iPerf3 assets (#407–#408), footer/state assets (#400), WireGuard export
fixtures (#355–#356), and QR asset preparation (#352–#353). Later runs passed
the respective gates; the active firmware baseline then passed the full
selected build and ZIP pipeline in #514. These older test failures are not
evidence of a still-failing current firmware path.

All 90 firmware run numbers in the queried history (listed to make the census
reproducible):

`#139–#143, #145–#146, #171, #194–#196, #199–#201, #217, #237, #242, #264, #275–#278, #288, #334–#346, #352–#353, #355–#356, #358, #365–#366, #384, #400, #403–#408, #431–#432, #443–#447, #449–#450, #466–#470, #479–#485, #489, #491, #493–#496, #498–#500, #505–#513`.

## Changes and boundaries

No new firmware source change was required in this review: the #513 defect is
already corrected by `a6edff8`, and #514 verified that commit. The checkout
currently has many independent modified and untracked project files; they were
preserved. Those local changes are not included in #514 and therefore are not
covered by its result. No workflow was cancelled or restarted, no files were
committed or pushed, and the router was not accessed or changed.
