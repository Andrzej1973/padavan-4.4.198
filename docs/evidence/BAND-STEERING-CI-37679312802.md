# Configuration snapshot and full compilation evidence

Inspected authoritative GitHub Actions REST run and job records on 2026-10-07.

## Corrected snapshot reader

- Run 37679312802: completed, success.
- Source: 40ffe0ce596fd6b17080cb5a47877c09de9af2d1.
- Job 112990896302: success.
- Verify immutable settings snapshot reader: success.
- Verify complete NVRAM snapshot overflow handling: success.
- Verify actual rc Wi-Fi lifecycle callbacks: success.
- Verify rc profile integration candidate: success.

This supersedes the failed snapshot reader check in run 37679022748. The fix bounds the WLAN name scan before searching for an equals sign, retaining the unterminated-name regression fixture. Snapshot capture is still not connected to the actual paired profile generation or complete Wi-Fi transaction. Passing this fixture does not establish immutable production configuration reads.

## Earlier full firmware and isolated rc build

- Run 37673562400: completed, success.
- Source: 5d515a13d263769f7e913277ed39350bb9d4eace.
- Firmware job 112971245536: success.
- Build WR1200JS firmware: success.
- Compile isolated full Band Steering drivers: success.
- Compile complete isolated rc with steering profile integration: success.
- Link isolated MT7621 systick candidate kernel: success.
- Verify ZeroTier source-built image and dependency closure: success.
- Firmware ZIP job 112987795206 and downloads job 112987795300: success.

The full rc result applies to the earlier initial endpoint revision. It does not prove full MIPS compilation of subsequent restart, boot, shutdown, child-exit or snapshot changes. Isolated candidates are separate from the production firmware; successful compilation does not establish their installation or device behavior.

## Pending kernel check

Run 37678044883, source 8dbc57feff3d7acf7b4729154632dca9d74e60e2, was still in progress at inspection. Its isolated kernel includes the candidate NVRAM overflow error change. No completed kernel result is claimed, and no restart or cancellation was issued.

## Next integration requirement

Capture one complete NVRAM dump for the coordinated transaction, validate compatibility from that same capture and generate both radio profiles from it. Preserve derived per-radio key_type behavior without mixing subsequent live reads into the snapshot. Snapshot lifetime must cover validation, quiescence and paired writes; capturing separately at validation and generation would leave the race unresolved. User AP.dat additions and external settings writers still require explicit treatment before production activation.
