# WR1200JS hybrid dashboard candidate

Owner authorized this dashboard alongside primary IoT work on 2026-11-12.
Visual reference is `docs/design/reference/dashboard-neon-uk-detailed.png`.

The candidate polls existing system, WAN and LAN status ASP endpoints and
links to Classic configuration pages. IoT and client attribution remain
unfinished. The existing Modern WebUI checkpoint remains preserved.

Run `node tools/hybrid-dashboard/check-dashboard.js` for response parsing,
CPU deltas, unavailable states, duplicate LAN entries and request timeouts.
`prepare.py SOURCE` installs assets and a ROMFS copy rule alongside Classic.
`check-image.py SOURCE` checks exact assets and required Classic routes.

Desktop Edge rendering at1280x900 and narrow rendering at500x844 were
visually inspected with missing ASP endpoints. Requested390px screenshots
used an actual492px viewport in Windows Edge and cropped the output.
True390px/mobile emulation remains unverified. The initial Node REPL browser
backend rejects the Linux workspace URI, so the Edge executable was used.

Firmware inclusion, browser telemetry on real ASP responses, authentication,
per-interface counts, complete service dashboard and hardware acceptance
remain pending. The local workflow edits have not yet been published.


The local shared monitor is `iot-status.html`, with 2.4 GHz main/IoT and5 GHz
main observations from the existing `/wr_devices.json` endpoint. Run
`node tools/hybrid-dashboard/check-iot-status.js` for snapshot attribution and
`node tools/hybrid-dashboard/check-iot-status-dom.js` for the actual controller
with injected DOM/fetch. The latter covers filters/search, stale clearing,
retry, duplicate request refusal and back-cache resume. Actual Edge1536/390
fixture rendering passed before the back-cache correction; evidence and its
limits are in docs/evidence/WR1200JS-HYBRID-MONITOR-BROWSER-2026-11-12.json.
SSID/radio state/PSM and embedded log telemetry remain unavailable. Target
image and router acceptance for the monitor are pending.
