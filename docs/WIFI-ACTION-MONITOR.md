# WR1200JS Wi-Fi action monitor

The homepage separates observed associations from Band Steering command evidence. Both sections refresh automatically and keep bounded history in RAM. They share a MAC filter and an explicit local JSON export.

## Evidence shown

- **Command requested:** the daemon attempted an allow/remove-candidate operation.
- **Driver ioctl accepted/failed:** the actual command transport result.
- **Driver candidate-table state verified:** a matching query was accepted by the existing grant controller. This confirms candidate-table state, not client association or roaming.
- **Observed band change:** two distinct successful radio snapshots confirmed a change. Its cause remains unknown.

Producer checks use kernel datagram credentials, the live executable inode, process start time and its retained exclusive lock. Session/sequence checks reject repeated or stale evidence. Collector interruptions, missing sequences, rejected messages and overwritten records are exposed explicitly.

## Bounds

The collector consumes at most 16 messages per five-second tick. Ownership is checked before and after each bounded batch. Separate rings retain up to 256 association observations and 256 command events. No history is written to flash. Polling pauses while the page is hidden.

Maximum-width serializer fixtures check the combined response against the browser limit of 131072 bytes. Actual CPU cost and behavior under router load still require device measurements.

## Verification and remaining work

[ABI 281](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38028371272) and [ABI 284](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38028824555) completed successfully, including registered target-package compilation, correlated grant-controller checks and actual prepared HTTP credential API probes. [Full build 137](WR1200JS-BUILD-137-EVIDENCE.md) successfully compiled the firmware and passed staged-image action observer checks.

Full firmware builds and real-device behavior must be verified separately. RSSI Kick action instrumentation is not connected to this command log yet. External access-point transitions are not observed. An accepted command or candidate-table confirmation must never be presented as successful roaming.

## RSSI enforcement source boundaries

Pinned MT76x2 and MT76x3 sources emit generic age-out before allocating a deauthentication frame. Allocation failure skips submission and table deletion. Frame submission is not a frame acknowledgement. MT76x3 also has a conditional WH_EZ_SETUP path that defers peer deletion. A future observer must capture MAC, BSS and client identity before deletion, report the RSSI reason separately from inactivity, and verify the actual deletion result. A call to MacTableDeleteEntry alone must not be reported as completed removal.
Both pinned MacTableDeleteEntry implementations clear the address before SET_ENTRY_NONE under the table lock and end with return TRUE. Therefore a TRUE return is insufficient evidence that the requested client was removed. Instrumentation must use the actual matched-entry clearing branch and preserve the address before it is zeroed.
