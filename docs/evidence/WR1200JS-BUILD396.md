# WR1200JS build 396 review — 2026-10-17

Run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39020375858
Commit: 822338940f64bed684f78a153dca81251a4cc890. Completed successfully.
Downloaded router-downloads artifact ID 12096836166 is not expired.

Image WR1200JS_4.4.198.9-396_82233894.trx: 12,602,575 bytes.
Recomputed SHA256 matches the image report:
eb570de35f78eb01e7722931aef3007333f12cce1439a89a2ed292061c3a243a
All six image structure/CRC checks passed. Guide identifies build 396 and this
commit. Config report: 112 options, zero mismatches, zero pending options.
WG/AWG and Band Steering selectors are enabled; kernel CAKE is unset.
VPN image cases passed 23/23; shipped MIPS manager cases passed 15/15.
Original reports are retained in build396/. No image binary is added to Git.

BusyBox audit explicitly leaves whole_service_audit_complete and runtime_verified
false. Image checks do not prove physical boot, settings preservation, new VPN
traffic, WebUI upgrade over VPN, or absence of steering noise on the router.
No flash, reboot or router configuration changes were performed in this review.

During acceptance-script review, total-log count subtraction was found to allow
false quiet results with a missing/rotating journal. The revised read-only check
requires a unique retained last-line cursor; loss/ambiguity/read failure is
UNKNOWN. It inspects only newly appended lines for both steering and reaper noise.
Host fixtures cover missing, empty, quiet, noisy, rotated, duplicated, deleted and
failed-wait journals. Service CI #187 passed at fc3467b:
https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39021734137
The job log confirms PASS post-flash journal window. This does not prove device quiet.
