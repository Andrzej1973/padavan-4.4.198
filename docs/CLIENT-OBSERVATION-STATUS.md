# WR1200JS client observations — current status

Updated 2026-10-14. The client list is part of the full WR1200JS port; its source and image evidence do not establish physical device acceptance.

## Current implementation

- The page requests data immediately on entry, then every 30 seconds after successful requests. Manual refresh is immediate and does not overlap another request. Failed requests use bounded retry backoff; hidden pages pause requests.
- Observations distinguish a Wi-Fi association from a networkmap observation, historical evidence and an unknown connection. Device OS/category classification is heuristic, not proof of identity. Grouping and filters retain their internal values when translated.
- EN/UK/RU labels cover list status, failure-stage messages, heading/help, table columns, network groups, categories, confidence, evidence descriptions and bounded-source notices.
- A source failure before any valid snapshot reports unavailable. After a valid snapshot it retains prior evidence as stale. It must not relabel retained evidence as a fresh connection.

## Diagnosing unavailable data

`wr_device_http_collect` first reads the locked networkmap source and then queries both enabled radios. A radio-query failure rejects the combined snapshot. This is a source-code finding, not proof of the cause on the installed image.

The JSON error includes an allowlisted stage: `networkmap`, `radio` or `initialization`. The page shows the corresponding localized explanation; unknown stage text is not displayed. An older installed image may return no stage. An authenticated page read or authorized local read of `/wr_devices.json` is needed to determine the actual failing stage. Networkmap file presence alone does not prove successful collection, and a successful RSSI endpoint does not prove the separate station-table query works.

After the owner restored access, a read-only SSH retry succeeded. The router reported kernel `4.4.198`, uptime `213533.79` seconds, networkmap PID 805, a regular 828-byte `/tmp/static_ip.inf` containing 19 lines, and both `ra0` and `rai0` network interfaces. A loopback HTTP read of `/wr_devices.json` returned exactly `{"error":"source_unavailable"}` without a stage. This confirms the endpoint still fails on the installed image; file presence and interface presence do not establish parser or station-query success. Stubby and DoH switches remained zero and `/proc/swaps` had only its header. No settings or services were changed. The live router remains an older test image, not these newly compiled changes.

## Evidence and remaining work

An additional live read found `rt_stream_rx=2`, `wl_stream_rx=2`, and all four queried radio switches (`rt_radio_x`, `wl_radio_x`, `mlme_radio_rt`, `mlme_radio_wl`) equal to 1. These values satisfy the current radio collector's stream-count precondition and do not select its disabled-radio path. `/wr_rssi.json` reported `cacheState=current`, both radios available/attempted with error zero; radio 0 retained one historical failure and one recovery, radio 1 none. This is evidence for the independent RSSI collector only. The separate structured station-table ioctl, networkmap parser and POSIX lock acquisition remain unverified on the installed image. Do not infer station collection success from RSSI health or the presence of the BusyBox `flock` command: the C networkmap collector uses `fcntl(F_SETLK)` directly.

[ABI CI 38501211651](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38501211651), commit `5709123b267f0ab914b5bd2991025a9bf430ec3d`, completed successfully. Local tests also exercised category-value preservation, translated OUI evidence text, stale/error handling and source preparation with actual donor homepage/HTTP source files. The image gate requires all registered status labels in shipped EN/UK/RU dictionaries and matching page attributes/assets.

[Full build 249](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38501211663) completed successfully. Its log reports `PASS staged homepage, exact assets and linked observation/action JSON markers` (34,804 raw asset bytes). The build manifest records `WR1200JS_4.4.198.9-249_5709123b.trx`, 13,142,595 bytes, SHA256 `863aff38865ca31e377ef67454ececfb86f6aff6f29acf7c087d3bf457508c91`. This hash is manifest evidence, not an independently downloaded image hash.

The subsequent change `ccc1ca3cd1b7d556fbabc33f7ab421eb29a9bdd5` retains the allowlisted collection failure stage alongside stale observations and clears it on recovery. [ABI CI 38502695491](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38502695491) completed successfully; [full build 250](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38502695605) was still in progress when checked. Build 249 does not contain this subsequent change.

Physical rendering, actual collection-failure stage, successful station-table reads, both-band membership, client movement, shared-Wi-Fi behavior and sustained router stability remain open. Do not mark these complete because localization or synthetic tests passed.
