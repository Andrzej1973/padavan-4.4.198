# Hybrid dashboard source investigation — 2026-11-12

The owner requested a lightweight dashboard with existing ASP endpoints and
Classic links. The pinned SDK source revision is
`c25283e915a2a00a763774dd255b14aff997285e`, web root
`trunk/user/www/n56u_ribbon_fixed`.

* `system_status_data.asp` emits `var si_new=<% json_system_status(); %>;`.
  Classic `state.js` calculates CPU busy percentage from successive
  `cpu.busy` and `cpu.total` counters and reads `ram.total`, `ram.used`,
  `uptime.days`, `uptime.hours` and `uptime.minutes`. A dashboard parser must
  validate the returned assignment and JSON, guard zero/negative counter
  differences and display unavailable data on fetch or parsing failure.
* `status_internet.asp` invokes `detect_internet()` and returns JavaScript
  assignment strings. `status_wanlink.asp` invokes `wanlink()` and
  `status_lanlink.asp` invokes `lanlink()`. Their emitted output and exact
  semantics require tracing the corresponding ASP functions before relying
  on them. A state-changing consequence of `detect_internet()` must be
  excluded before scheduling polling.
* Classic `device-map/clients.asp` obtains clients using `getclients(1,0)`.
  That observation alone does not establish per-interface ra0/ra2 attribution.
  Existing device status and 2.4 GHz wireless pages are available as links.
* Current `prepare-production.py` adds a custom `/wr_modern.json` handler in
  `web_ex.c`. The owner requested no GoAhead C backend changes for the hybrid
  dashboard. A dedicated hybrid entry needs a separate asset installer using
  existing endpoints, preserving the existing Modern checkpoint and Classic.

This is source evidence only. Authentication, final ROMFS inclusion, network
responses, IoT interface availability and device runtime are unverified.

A first standalone candidate is in `tools/hybrid-dashboard`. Its three assets
are 4,391 bytes and poll the existing system status endpoint, with explicit
unavailable states and links to pinned Classic pages. WAN/LAN summaries and
per-interface client counts remain to be implemented after tracing their data
sources. The candidate has not been installed in the firmware or browser-tested.

WAN status now uses the existing `wanlink()` code from `status_wanlink.asp`.
Pinned `web_ex.c` defines code 0 as connected and codes 1–9 as failure or
waiting states. The candidate extracts the numeric function return as text and
never executes the response as script. Unknown codes remain unavailable.

LAN port text is emitted by `lanlink_hook` in `web_ex.c` and populated by
`switch_mtk_esw.c:fill_eth_port_status`. It uses `No Link`, speed/duplex
strings or `I/O Error`. The candidate treats errors and unknown strings as
unavailable, avoiding a false connected-port count. Device mapping remains
runtime-unverified.

`tools/hybrid-dashboard/prepare.py` installs the candidate alongside Classic
using the existing ROMFS copy mechanism. An isolated fixture verifies asset
copy, preservation of Classic and duplicate-install refusal. The workflow has
not yet been changed to invoke the installer, and image/runtime checks remain.

`lan_clients.asp` emits `get_static_client()` into `ipmonitor_last`, and
Classic `getclients()` joins its MAC addresses against a separate wireless
map. This source does not identify ra0 versus ra2, so the dashboard keeps
client status as a Classic link until a per-interface source is verified.

The existing `/wr_devices.json` collector queries the radio MAC table and
exports `band` plus `apIndex` for associated stations. The serializer marks
indices above 1 as unknown rather than assigning IoT, and a successful query
on the main interface has not been shown to include ra2 stations. The source
is a candidate for ra0 counts, subject to current/nontruncated snapshot checks.
Do not infer ra2 completeness from an empty list. This HTTP endpoint is an
already existing project feature, not a new GoAhead modification for hybrid.

Pinned `mt76x3/common/cmm_info.c:RTMPIoctlGetMacTableStaInfo` walks the
whole MAC table for non-APCLI queries, selects associated clients and exports
`func_tb_idx` as `ApIdx`. `ap/ap_cfg.c` maps the collector ioctl to that
function. This establishes source-level BSS attribution for the pinned
vendor driver. Snapshot truncation, disabled-radio semantics, HTTP freshness
and actual ra2 operation must still be handled before showing a zero count.

`wr_device_collect_radio` replaces a disabled radio with an empty snapshot,
while `/wr_devices.json` exposes no separate radio-query availability flag.
Therefore even a current, nontruncated empty snapshot cannot establish a live
zero station count. Retain the Classic client link until the UI can distinguish
disabled radio, successful empty query and the IoT BSS runtime state.

The local WR1200JS workflow now invokes the hybrid installer and checks
its assets and Classic routes in ROMFS. A simulated ROMFS assembled from the
pinned Classic tree passes. This local workflow edit coexists with prior
unrelated local changes and has not been published or exercised by CI.
