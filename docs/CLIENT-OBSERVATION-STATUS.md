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

The latest attempted physical read timed out at SSH connection establishment; no new source-stage result was obtained. The live router remains an older test image, not these newly compiled changes.

## Evidence and remaining work

[ABI CI 38501211651](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38501211651), commit `5709123b267f0ab914b5bd2991025a9bf430ec3d`, completed successfully. Local tests also exercised category-value preservation, translated OUI evidence text, stale/error handling and source preparation with actual donor homepage/HTTP source files. The image gate requires all registered status labels in shipped EN/UK/RU dictionaries and matching page attributes/assets.

Full build 249 was still active on the latest check. Its result and exact packaged assets remain to be inspected. Physical rendering, actual collection-failure stage, successful station-table reads, both-band membership, client movement, shared-Wi-Fi behavior and sustained router stability remain open. Do not mark these complete because localization or synthetic tests passed.
