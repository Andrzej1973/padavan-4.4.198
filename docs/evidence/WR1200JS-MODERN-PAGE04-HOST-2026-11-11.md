# Accepted page04: Wi-Fi5 General source/host checkpoint

Accepted references and hashes: docs/modern-design/04-WIFI-5-GENERAL-UK.md.
Renderer now uses band-specific general cards, with two columns for5GHz:
radio/identity/security left, radio parameters/schedule right. Full navigation,
IoT reservation and real per-band Classic destinations retained. This is still
read-only; no form, Apply action, secret retrieval or mutation was introduced.

Public JSON allowlist adds country_code/radio_date_x/radio_time_x/radio_time2_x
for each band. Original11 mandatory public keys remain; four new keys are
optional in client projection for older read-only responses, missing/non-string
values become unknown. No NVRAM enumeration. Country displayed as stored code,
not an assumed country name or regulatory availability. Existing shared-name
notice is conditional; SSID byte count uses UTF8. Other independent controls
remain per band. New radio modes/width labels describe stored values, do not
provide unverified choices;160MHz is not offered or advertised.

Pinned Classic source Advanced_Wireless_Content.asp SHA256:
e36f332df5b204e4db904e9c80aacfcb6dd8623b8e64c70016780b1777b1de88.
All four wl_ keys occur in actual Classic page. Schedule uses existing validated
Sunday-first7-bit/HHMMHHMM decoder; shows days and weekday/weekend intervals,
unknown malformed states and system-time note. A separate schedule master toggle
is not invented from the drawing; its exact backend semantics still need audit.

Checks passed: actual C JSON ASan/UBSan with strict15-key public allowlist and
existing credential/Guest/form suites; Node actual renderer across15routes;
page02/04 shared/open/missing/unknown/legacy/20MHz states; correct5GHz mode,
region/time values, disabled controls, no forms/buttons/secrets; Wi-Fi routing
and shared planner regression; whitespace. Tests use DOM fixtures, not a real
browser or device. Target/image inclusion for this new package remains pending.
Further work: visual desktop/mobile comparison, precise master-schedule source
semantics and backend Apply acceptance before enabling editing. Full Modern-only
coverage and full firmware/runtime acceptance remain open.

Cleanup: Node checks used memory only; C fixture temporary directory auto-removed
by existing check_json.py. No new retained build tree or copied PNG. Original
images and pinned source archive retained as required inputs.

## Radio schedule semantics audit

Pinned net_wifi.c SHA25698bbe9cfca0af35be4ddb82742022b90cc51c2f7b34834e627ee6c5f2187dc69.
At921–929, is_radio_allowed_wl/rt directly call timecheck_wifi with the three
radio_date_x/radio_time_x/radio_time2_x fields. Watchdog uses these wrappers
at306/348 and reload at422/435. Classic initializes wl_radio_x and wl_closed
switches (line29); its schedule is the day mask and two intervals, not a separate
radio-schedule-enable NVRAM key. Defaults218–220 and325–327 are1111111 and
00002359/00002359. This source path provides no independent schedule master.
Do not invent one from the reference drawing or conflate it with radio power.

check_guest_rc_schedule.py now supports --radio: executes actual timecheck_wifi
through the actual two radio wrappers, with clock/NVRAM substitutes. Minute-wise
checks cover both bands/all days, inclusive boundaries, Friday overnight,
no selected days and all-days00002359. Actual legacy malformed-length mask
permits work; UI marks malformed input unknown and does not claim it disables
radio. No driver/RC behavior was patched. Existing Guest mode also rerun and
passes, preserving prior behavior. ASan/UBSan and warnings-as-errors pass.

Reproduce with pinned archive path and --radio; omit flag for original Guest
regression. Owned radio scratch51865B and Guest scratch51530B inventoried,
auto-removed and absence asserted. Source archive retained. This is source/host
semantics, not execution of watchdog or radio on WR1200JS. Desktop/mobile visual
check and image/device acceptance remain pending.

## Actual Edge visual check

Opt-in check_page04_browser.py serves actual assets and explicit fixture JSON
on loopback, starts a fresh isolated Windows Edge profile and uses CDP via
Windows PowerShell to emulate exact1536/390px viewports. No router connection.
A test-only banner labels screenshots as local fixtures. Parsed metrics confirm
actual innerWidth1536/390, document/client width1521/1521 and390/390, no global
horizontal overflow, expected cards/region/intervals/shared notice, all inputs
disabled, zero Wi-Fi forms/buttons. Both final screenshots visually inspected:
two columns desktop and stacked mobile; section tabs scroll locally.
No claim of pixel-identical full shell or physical phone/router acceptance.

Fixed duplicate professional-card text that incorrectly redirected the already
visible5GHz schedule. Node15-route and page02/04 conditional regression passed
again. Final browser assertions passed after correcting PowerShell UTF8/report
output handling; earlier harness failures are not counted as passing tests.
Report: WR1200JS-MODERN-PAGE04-BROWSER-2026-11-11.json with asset/screenshot hashes.
Fresh browser profiles37467850B removed after process termination. After visual
inspection and independent zero-active-phase-browser check, seven screenshot/
report files3084847B removed by exact inventoried paths; three phase directories
absent. Compact evidence/source kept, original design images untouched.
