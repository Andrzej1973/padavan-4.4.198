# Padavan Modern local preview (stage 1)

## Wi-Fi architecture demo — 2026-10-19 update

The latest user task extends the previous home-only scope with isolated Modern
Wi-Fi pages. Start with `start.bat` as below, then open
`http://127.0.0.1:8080/modern/#wifi/common` or click **Бездротова мережа**.
Three sections: shared basics, independent bands (six subsections each), and
an explicitly unverified IoT draft. Back/forward and visible back links work.
Drafts live in memory only and disappear on page reload. Use dummy credentials.
Buttons simulate a preview confirmation; no router configuration is saved.
Production Classic files and the existing save path are untouched.

Read `../../docs/WEBUI-MODERN-WIFI.md` for the source mapping and limits:
radio enable/hidden SSID are not part of the existing shared backend; IoT
isolation is not accepted; Enterprise/WEP, dynamic driver dependencies and
MAC/WDS list operations are not implemented in the Modern demo yet.

Checks: `node check_wifi.js` and, with the server running,
`py -3 verify_preview.py`. To regenerate the static inventory from the saved
build-410 Classic files, run `py -3 build_wifi_schema.py`; normal preview launch
does not require those archived files. Python and Node checks need no packages.

The original home-stage notes below describe the earlier checkpoint. References
to a sole page or no forms now apply only to the homepage, not Wi-Fi drafts.

This is a standalone, read-only Windows preview of an early Modern homepage concept. It is not the completed Modern homepage or title page, is not included in firmware builds, and does not contact, configure, reboot, or flash a router. Padavan Classic production pages and behavior are unchanged. Per `docs/WEBUI-MODERN-HOME-SCOPE.md`, complete and verify the IoT network first, then finalize the Modern mockup and preview, and create the title page afterward.

## Start on Windows

Requirements: Python 3 (`py -3` launcher or `python`). No third-party packages are used.

1. Open `tools\webui-preview` in File Explorer.
2. Double-click `start.bat`.
3. Keep the console window open and visit `http://127.0.0.1:8080/modern/` in the browser. The server binds only to loopback (`127.0.0.1`), so other devices on the LAN cannot connect. No Windows Firewall exception or administrator rights are required for the normal local preview. Do not create a broad inbound rule or allow Python on Public networks. If port 8080 is occupied, close the other local server or set `PADAVAN_PREVIEW_PORT` in the launching environment first.
4. Press `Ctrl+C` in that console window to stop the server. If Command Prompt asks `Terminate batch job (Y/N)?`, answer `Y`.

Alternatively, run `py -3 server.py` from this folder and press `Ctrl+C` to stop it. Python 3 must be installed on the Windows computer running the preview; check with `py -3 --version`. A Python installation is not bundled with this project.

## Scope and evidence

- The durable design goal and first-stage boundaries are recorded in `docs/WEBUI-MODERN-HOME-SCOPE.md`.
- `public/index.html`, `public/styles.css`, and `public/app.js` contain the sole Modern screen: the homepage. `data/dashboard.json` contains separate, visibly marked mock data and a configurable list of unconfirmed service-tile placeholders.
- The screenshot provided for this task is the visual reference. Its values are treated as mock values, not measured WR1200JS capability or live device state.
- No IoT card or IoT clients are shown in this early preview. Add the IoT card only when IoT is implemented and verified; then finalize the mockup before creating the title page.
- The Classic source inventory is based on `docs/WEBUI-COVERAGE-INVENTORY.json` (base commit `c25283e915a2a00a763774dd255b14aff997285e`). It lists 147 WebUI source/resource files. Main menu target pages include `index.asp`, `Advanced_WAN_Content.asp`, `Advanced_Wireless2g_Content.asp`, `Advanced_Wireless_Content.asp`, `Advanced_APLAN_Content.asp`, `Advanced_Firewall_Content.asp`, `Advanced_SQM.asp`, `Advanced_System_Content.asp`, `Advanced_Services_Content.asp`, and `Main_LogStatus_Content.asp`.
- The sidebar items are present and identify those real Classic destinations, but they show an explanation instead of pretending to render router ASP pages. Full Classic remains available in the actual firmware. The preview's Classic control explains this limitation; it does not change the router or stored theme.
- Header controls and service tiles are non-operational. No service is enabled. There are no forms or remote actions. The footer has one read-only link to the GitHub Releases list; it opens in a new tab, and firmware downloads/installation remain manual.
- The HTTP server serves only local files and demo JSON on `127.0.0.1`. It allows only GET and HEAD; POST, PUT, PATCH, DELETE and OPTIONS are rejected server-side with 405. It does not proxy or contact `192.168.20.1`.
- ASP/CGI execution, real configuration, live router status, credentials, client data, real CPU/RAM/zram/USB metrics, and actions cannot be validated in this preview. No full firmware compilation is needed or run.

## Checks

With the server running, run `py -3 verify_preview.py`. This checks local HTTP resources, demo-only data, absent forms, the single approved GitHub Releases link, the intentionally deferred IoT section, unknown-page handling, and server-side rejection of mutating methods. See `VERIFICATION.md` for the prior implementation results and checks that remain unavailable.
