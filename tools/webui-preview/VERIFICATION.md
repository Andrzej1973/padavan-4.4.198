# Padavan Modern preview — verification

Date: 2026-10-19

## Prepared production shell — 2026-10-31

`prepare-production.py` installed the static shell and authenticated JSON route
into a disposable copy of the pinned Padavan source. `check-production.py`
verified that the `/modern/*` assets exist, the page has no mutation form, the
Wi-Fi schema is marked live-read-only, and `do_wr_modern_json` is registered as
an auth-required `application/json` MIME handler.

The C JSON emitter passed strict host GCC and emitted valid JSON in live mode.
The fixture covered 11 pages, 14 service tiles, WAN/LAN/Wi-Fi NVRAM values,
memory and uptime, with IoT explicitly unverified. The production-shell browser
test loaded the rewritten `/modern/index.html`, authenticated live-JSON fixture,
Wi-Fi schema and all local assets with no console errors. It displayed
`PADAVAN MODERN · LIVE READ-ONLY`, `LIVE` chips, the WR1200JS title and no
residual fallback `DEMO` banner.
`verify-production-shell.py` also passed health, rewritten asset requests,
live JSON shape and 405 rejection for POST/PUT/PATCH/DELETE/OPTIONS.

Not performed: target MIPS compilation of `web_ex.c`, firmware build, ROMFS
inspection, authenticated router request or on-device runtime. The build
workflow does not yet invoke the installer.

## Full preview structure — 2026-10-31

The local Modern preview now exposes eleven informational pages matching the
approved reference structure: WAN, IoT, LAN, VPN, DNS/proxy, services,
monitoring, firewall, QoS, system and log. Wi-Fi retains the existing shared,
split-band and IoT draft paths. The dashboard adds the top 2.4 GHz / 5 GHz / IoT
switcher, WAN traffic graph, process-load rows and explicit `Н/Д` temperatures
when no verified source exists. The inconsistent DEMO USB state was corrected.

Checks completed:

- `node --check public/app.js` and `node --check public/wifi.js` passed;
- `node check_wifi.js` passed all 15 Wi-Fi routes and shared-field constraints;
- `python verify_preview.py` passed health, local resources, eleven page
  definitions, DEMO/IoT boundaries, service tiles and mutating-method refusal;
- `python check_references.py` passed all six owner-supplied reference images;
- browser checks opened all eleven informational routes and five representative
  Wi-Fi/IoT routes with the intended title, active page and no console errors;
- the local SVG favicon returned 200 and removed the remaining 404 request;
- desktop checks kept document width equal to viewport width;
- a 390×844 responsive check kept document width equal to viewport width,
  rendered all thirteen navigation entries and retained the `Н/Д` temperature
  policy; the temporary viewport override was reset.

All page contents remain local DEMO data. No ASP/CGI handler, NVRAM key,
service, firewall rule, DHCP server, router endpoint or production Modern asset
was changed or verified by this preview work.

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
- a 390×844 viewport showed a single-column network overview and two-column
  navigation without horizontal overflow; the temporary viewport was reset.
- clicking the Zapret2 service tile opened the preview-only Classic destination
  notice and identified `Advanced_Services_Content.asp#zapret2_enable_on_of`;
  it made no router request.

The IoT card is marked “Не підтверджено” and says runtime is not accepted. This
layout remains a local preview and does not prove production Modern integration.
