# Padavan Modern preview — verification

Date: 2026-10-19

## Completed

- Python syntax: `server.py` and `verify_preview.py` compile successfully with the bundled Python 3.12.14 runtime.
- JavaScript syntax: `node --check public/app.js` passes.
- Local HTTP: `http://127.0.0.1:8080/modern/` and `/__health` return 200.
- Windows console lifecycle: `start.bat` starts the server in its own console, and Ctrl+C stops it. The local run is kept active for preview; the console method avoids process-kill permissions.
- Owned local assets: `styles.css`, `app.js`, and `/api/dashboard.json` return 200.
- Unknown path: returns 404; no mock Classic page is served.
- Form/actions: no forms or remote actions are present. The footer contains one link to the repository's GitHub Releases list. Server responds 405 to POST, PUT, PATCH, DELETE, and OPTIONS.
- Demo boundary: JSON carries `"demo": true`; all 12 service tiles are marked unconfirmed; only two Wi-Fi bands are shown, and IoT is deliberately deferred.
- Classic navigation: selecting Internet opens the clear “unavailable in preview” notice and names the real target `Advanced_WAN_Content.asp`. No request is sent to the router.
- Responsive browser measurements (viewport width / document scroll width): 375 / 356, 768 / 750, 1280 / 1280, 1920 / 1920 CSS px. None exceeds its viewport width.
- Visual browser review: desktop and mobile layouts display the loaded demo data and the reference-style dark blue dashboard. No visible JavaScript error state appeared.

## Not verified

- Browser developer-console log inspection was not available through the connected browser control, so console cleanliness is not claimed. The page did load its script and populate all cards in the browser.
- ASP/CGI execution, the real router’s state, service capabilities, authentication, persistent settings, and target hardware are outside this static preview.
- No firmware build or device operation was run.
# Wi-Fi architecture checkpoint — 2026-10-19

Executed on Windows:

- `py -3 build_wifi_schema.py`: 207 controls inventoried from 12 saved Classic
  pages; per-page SHA256, no ASP or NVRAM values copied.
- `node --check public/wifi.js`: passed.
- `node check_wifi.js`: 15 routes, six subsections per band, pure navigation,
  existing shared planner validation, six-field sync, independent advanced/IoT
  data retained, invalid PSK rejected before copy; TXBF/AX excluded, TX/RX <= 2.
- `py -3 verify_preview.py` against the live loopback server: resources and
  demo schema passed; POST/PUT/PATCH/DELETE/OPTIONS return 405; unknown ASP 404.
- `git diff --check`: passed, with existing CRLF normalization notices.
- In-app browser: edited 2.4 GHz SSID, opened Professional and returned — draft
  retained. Edited TX, applied shared SSID through warning/cancel/confirm — both
  bands synchronized while TX stayed independent. Shared fields lock on band
  page; IoT retains its independent SSID. Browser Back and Forward passed.
  Reload resets drafts as documented. Reload also showed only TX options 1/2.
- Opened all 12 band/subsection pages in the browser. Each rendered its fields;
  browser error log was empty. Saved the common-page screenshot as
  `wifi-demo.jpg` and left the preview tab open.

Not performed: firmware compilation, router changes, production ASP/CGI apply,
physical Wi-Fi/IoT isolation tests, or complete Classic conditional behavior.
Advanced/guest/bridge/MAC/RADIUS screens are structural inventory forms; their
full validation and list operations are not implemented. No new support claim
is made for inherited controls. See `docs/WEBUI-MODERN-WIFI.md`.

Earlier checkpoint follows.

## Service-tile update — 2026-10-25

The twelve generic placeholders were replaced with fourteen services selected in
the WR1200JS profile: Stubby, DoH, WireGuard, AmneziaWG, ZeroTier,
Shadowsocks, Privoxy, WPAD/PAC, HTTP/HTTPS, SSH, iPerf3, Cron, KMS and Zapret2.
Each tile has `availableInBuild:true` and `runtimeVerified:false`; the preview
therefore describes build availability only, not working device state.

## Reference-layout dashboard — 2026-10-25

The homepage now uses the supplied two-column direction: Internet, 2.4 GHz,
5 GHz and an explicitly unverified IoT card on the left; quick-service tiles on
the right; system metrics below the network overview. Ukrainian decimal commas
are used in band and memory labels.

Browser and local checks:

- `node --check public/app.js` passed;
- `python verify_preview.py` passed HTTP resources, DEMO/IoT boundaries,
  selected-service tiles and mutating-method rejection;
- `node check_wifi.js` passed all 15 band routes and shared-field constraints;
- `python check_references.py` passed all six owner-supplied PNG hashes;
- visual inspection showed the four overview cards, system panel, fourteen
  service tiles and Ukrainian labels without horizontal overflow at the
  available desktop viewport.

The IoT card is marked “Не підтверджено” and says runtime is not accepted. This
layout remains a local preview and does not prove production Modern integration.
