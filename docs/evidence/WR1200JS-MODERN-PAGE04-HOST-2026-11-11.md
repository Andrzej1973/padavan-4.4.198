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
