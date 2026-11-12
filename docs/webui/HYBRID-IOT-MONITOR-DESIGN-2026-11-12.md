# Wi-Fi and IoT monitor visual reference

The owner supplied the finished drawing on 2026-11-12 after the monitor brief.
Preserved reference is `docs/design/reference/iot-wifi-monitor-uk.png`.
Original filename is `a_detailed_ui_mockup_collage_of_a_router_web_inter.png`.
SHA256 is `a0e5688cf409e987c2fa33a7cecf65be36408937158b62988d75fea7adc5bb66`.

The drawing covers desktop and mobile layouts, ra0/ra2 cards, client filters,
search, IP/MAC/RSSI/PSM columns, driver log controls and loading/empty/error/
unavailable states. Example clients and log events are explicitly demonstration
content. Use the main desktop panel as the page layout. The adjacent state
panels describe mutually exclusive states.

The IoT status dropdown in the drawing is represented as read-only status in
the implementation. Configuration remains behind Classic links, as required
by the monitor brief. PSM and driver logs require verified existing data
sources. Missing telemetry must display unavailable values. Device identity,
current association, snapshot freshness and BSS attribution require validation
before client counts or sleep state are displayed.

Design received and visually inspected. Implementation, browser verification,
firmware integration and device acceptance remain pending. Primary IoT driver
work continues while this page is prepared during CI waits.


## Owner-approved 5 GHz extension — 2026-11-12

The shared monitor includes three network cards in the supplied visual style.
Use Ukrainian labels «Основна мережа 2,4 ГГц», «IoT 2,4 ГГц» and
«Основна мережа 5 ГГц». Each card displays SSID, observed availability/state
and associated-client count when verified telemetry supplies those values.

The shared client table gains a «5 ГГц» filter alongside «Усі», «Основна
2,4 ГГц» and «IoT 2,4 ГГц». Network badges identify both band and BSS.
Classify stations using verified radio band and AP index together, because
an AP index alone can occur on both radios. Keep MAC/IP/RSSI and available
PSM information in the existing columns. Represent unavailable PSM explicitly.

Use three columns when width permits and stack cards on narrow screens.
Retain search and the shared bounded log panel. Log attribution and telemetry
availability are verified separately for each radio. Reuse the accepted
reference image for this extension. A second drawing is optional.

This addition is approved design scope. Its implementation and live telemetry
verification remain pending.


## Local monitor implementation checkpoint

`tools/hybrid-dashboard/iot-status.html` now provides the three-card responsive
monitor with shared client table, network/search filters and manual/automatic
refresh. It reads the existing `/wr_devices.json` response. Band plus AP index
select 2g/0, 2g/2 and 5g/0. Associated current observations are accepted only
from current, nontruncated, zero-invalid snapshots with age at most15 seconds.
Duplicate per-network MAC identities reject the response. Device strings use
textContent. Stale networkmap IP and missing RSSI display unavailable values.
Empty snapshots leave counts unavailable because radio availability is absent
from this endpoint. SSID, radio state, PSM and embedded log telemetry remain
unavailable. The log panel links to the existing Classic system log.

Polling uses one in-flight request, an8-second abort through body reading and
a10-second visible-page interval. The installer and ROMFS verifier include all
six assets and preserve Classic routes. Combined raw assets total18,214 bytes.
Node parser/filter checks and the existing dashboard suite pass. A temporary
source/ROMFS fixture verifies installation and exact asset copies. Browser
rendering, real HTTP responses, target image inclusion and device behavior
remain unverified for this local change. No production telemetry backend was
added. Temporary fixtures were removed automatically.

The existing CI dashboard test entry now also runs both monitor test suites.
