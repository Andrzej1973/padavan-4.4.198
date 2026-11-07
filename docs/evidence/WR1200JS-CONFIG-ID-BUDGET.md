# MT7603 startup checked-ID budget counterexample

Source audit of freshly generated candidate at repository `206ef4a`,
2026-11-06. This is a conditional source-path counterexample, not runtime
reachability evidence for the owner's current settings.

`common/rtmp_init_inf.c` invokes `AP_AUTO_CH_SEL` during startup when automatic
selection is requested. `include/ap_autoChSel.h` maps it to
`APAutoSelectChannel`. In `ap/ap_autoChSel.c`, that function loops over
`ChannelListNum` unless random selection on the A band takes the other branch.
Every loop iteration calls `AsicSwitchChannel`.

`hw_ctrl/cmm_asic_mt.c` dispatches that call through `ChipSwitchChannel`.
MT7603 registers `mt7603_switch_channel` in `chips/mt7603.c`; both bandwidth
branches submit one channel-switch and one TX-power command. Both consume a
checked sequence in the owned config path. The SDK 2.4-GHz region-0 channel
descriptor contains 11 channels, and region 1 contains 13 (`common/rt_channel.c`).

Thus the scan alone requires 22 or 26 checked transactions for these source
branches, exceeding the 15 one-use checked IDs even before other startup
commands. Eight fully attempted scan iterations already require 16. Earlier
failure may stop submission sooner; it does not make the intended successful
startup fit. An outer-loop bound or a claim that startup needs fewer than 15
commands cannot justify opening the current gate.

Preserve late/duplicate ACK protection. Supporting these settings requires a
verified protocol epoch/reuse strategy or another proven completion identity;
silently disabling automatic selection would change the owner's settings and
does not satisfy the port objective. EDCA/slot execution proof was a
separate requirement; the later owned direct-MMIO/readback implementation and
its isolated target checks must be assessed separately from this ACK budget.

## Wire field versus supported sequence domain

The SDK `include/mcu/andes_mt.h` declares both TX and RX `seq_num` fields as
8-bit fields. That makes IDs 16..255 representable on the host wire layout,
but does not prove that the loaded MT7603 firmware preserves or supports them.
The existing 1..15 allocation domain must not be widened from the C bitfield
alone. Firmware-specific evidence of full-byte echo, reserved-value semantics
and event matching is needed first. Even a validated 255-ID domain would be a
bounded budget, not indefinite safe reuse or a replacement for late-response
protection.

The common extended-result payload contains command ID, three reserved bytes
and status. It carries no declared request cookie, channel or TX-power tuple.
Those fields therefore provide no existing per-request generation identity
when the same command and sequence are reused. Reserved bytes cannot be used
as a cookie without an independently established firmware contract.

## Existing retirement boundary is a boot boundary

`mcu-boot-retired-boundary.inc` permits clearing retired IDs only before
controller recreation: MCU_INIT must be clear, IRQ/DMA/RX/controller states
must be zero, ROM observation must match the boot ticket, and the PSE must be
empty. Config ownership instead requires FW_RUN_TIME, initialized controller,
restarted RX, DMA and filtered IRQ state. These contracts are incompatible at
the same instant. Calling the existing retirement helper between scan commands
will refuse; relaxing its guards would remove the evidence on which it relies.
Returning to ROM/reloading firmware would require proving preservation or
reapplication of the calibration/configuration already sent and would not by
itself provide transparent batching. No such implementation is established.

## Bootstrap consumes the same ledger

The Method1 private loader performs ROM observation/hardware preparation (which
contains the retired-ID boundary), then `CmdAddressLenReq`, scatter transfer,
and `CmdFwStartReq` before committing the firmware receipt. Address/length and
FW_START wait for checked replies; scatter packets do not reserve checked IDs.
Thus this successful source path consumes at least two IDs after the boundary,
leaving at most 13 of the 15 for configuration. A restart request, when needed,
precedes that boundary and must not be counted as a fresh config ID.

After the receipt, private MCUSysInit performs the owned DMA scheduler operation
and returns to the outer init/config-owner begin. No additional MCU command is
present in that direct handover path. Receipt snapshots are necessary because
requiring an empty retired mask at config begin rejects valid checked boot
commands; snapshots preserve their IDs rather than replenish the budget.

This is a source-path count, not a complete worst-case count for all loader
variants or configuration commands. The 22/26-command scan counterexample is
therefore already excessive even without counting EEPROM/PHY initialization.

### Host regression verification (2026-11-07)

`check-mcu-config-transport.py` now exercises the real config-owner begin/finish
and TX-power builder with injected transport: bootstrap receipt mask `6`,
cursor `2`, followed by thirteen successful checked reservations/replies.
The ledger reaches `0xfffe`; the real sequence reservation helper refuses
another ID, while the receipt remains mask `6`, cursor `2`. This proves budget
retention in this host composition, not safe reuse or successful full startup.

The full host transport suite passed on the retained generated candidate
`/tmp/wr-iot-tx-owner.DR53cL/mbss-poll-caller`, substituting the current
config-owner readiness fragment in memory because that candidate predates the
receipt change. Transport, registers and hardware remain injected. A fresh
generated target build is still required; this run is not image/runtime proof.

## Channel privilege is not an established replacement completion identity

Pinned SDK `mcu/andes_mt.c:1137` defines `CmdChPrivilege`; its request layout
in `include/mcu/andes_mt.h:393` includes `ucTokenID`. The builder zeroes the
request and never assigns that token. It initializes the command without a
wait, response length or callback. This is a separate command (`0x20`), not
the checked extended channel switch (`0x08`).

`UnsolicitedEventHandler` routes event `0x18` to `EventChPrivilegeHandler`
(`mcu/andes_mt.c:2804`). That handler does not inspect `Data` or `Length`;
it updates RMAC RX stream bits from controller state. The pinned SDK therefore
does not establish a token echo, channel echo, response status, event layout,
or ordering guarantee that could retire the channel/TX-power transaction.
The only other C call site found is commented out in ATE. Do not substitute
this command or treat the unsolicited event as a general execution fence
without a firmware-specific contract and independent verification.

## Firmware identity boundary

`inspect-mt7603-firmware.py` identifies the two embedded initializers in the
pinned c25283e driver. E1 is `_e1_drv_tv`, build `20140313215548` (64,132 bytes);
E2 is `CL173766_R`, build `20171110105932` (74,372 bytes). Exact header/image
SHA256 and Method1 transfer lengths are recorded in
`WR1200JS-MCU-FIRMWARE-IDENTITY.json`. Both parsed image hashes/lengths were
independently matched against C-compiled initializers on the host. Compiler
outputs were temporary and removed. CRC validity is not established by this
check.

The SDK chip-capability initialization selects E1/E2 by revision predicates;
Method1 may instead load an external file under BIN_FILE_METHOD. This inventory
therefore does not establish the firmware actually running on the owner's
router, nor the firmware ACK reuse/duplicate contract. Do not transfer claims
from a similarly named upstream image without matching its bytes and protocol.
Optional CI now retains the pinned embedded-image identity report alongside
its diagnostics; this report alone is not firmware execution evidence.

## Fresh upstream comparison (2026-11-07)

Inspected OpenWrt mt76 revision `0936617dc529ff9da0385221d3fa6de732231177`
through the GitHub API with immutable revision selection. Source hashes and
line references are in `WR1200JS-MCU-UPSTREAM-ACK-AUDIT.json`.
The MT7603 sender cycles nonzero four-bit sequences. Its parser compares the
response sequence and marks MCU hang on timeout. The common sender holds a
mutex through send/response processing and discards mismatched replies.

This is useful precedent for serialized transport but does not establish a
firmware-specific duplicate-response lifetime bound or generation cookie.
The upstream image bytes have not been matched to our E1/E2 embedded images.
It does not justify clearing the current retired ledger or relaxing the
existing stale-ACK tests. No upstream code was transplanted.

Sources: [MT7603 MCU](https://github.com/openwrt/mt76/blob/0936617dc529ff9da0385221d3fa6de732231177/mt7603/mcu.c),
[common MCU sender](https://github.com/openwrt/mt76/blob/0936617dc529ff9da0385221d3fa6de732231177/mcu.c).

## Command-class partitioning is not an immediate reuse fix

Common extended result byte0 distinguishes channel, TX-power and EFUSE
commands. However, both current checked RX paths set response_done and default
to failure on the first same-sequence packet before testing that echo. An old
response of another class therefore terminates the new waiter as failed;
merely partitioning retirement masks would introduce false failures. Also,
repeating the same class still has a finite15-ID budget. Any class-aware
strategy must first establish admission/mismatch handling for every RX path
and count all startup/overlap/restore calls. No partition or reuse enabled.

## Exact upstream image comparison (2026-11-07)

Fetched only the two firmware blobs from immutable OpenWrt mt76 revision
0936617dc529ff9da0385221d3fa6de732231177 into memory. E1 SHA256 exactly
matches the pinned SDK initializer. E2 does not: upstream has 72,180 bytes,
version `ap_pcie`, build20160107100755, SHA256
1710d02af192d2a274459c76d15d180d84c44bc7811e7e6f3c271245a8bbe5c9;
our E2 has 74,372 bytes, CL173766_R/build20171110105932. Full source URLs and
embedded/reference hashes are in WR1200JS-MCU-UPSTREAM-FIRMWARE-COMPARE.json.
This supersedes the previous statement that neither image had been matched.
E1 provides same-image implementation precedent for upstream ID cycling; it
still does not prove a maximum late/duplicate-response lifetime. E2 has no
same-image comparison to that client. Neither image was replaced, installed
or retained as a new binary; actual router image selection remains unverified.

## Same-class ACK replay negative controls (2026-11-07)

The generated locked ACK fixture and actual allocation-free direct RX fixture
now replay the same captured successful common result into two separately
initialized host requests with the same sequence and command. Both paths
accept it for channel0x08, TX-power0x11 and EFUSE0x21. ASan/UBSan runs passed on
the retained candidate. These are deliberately labeled negative controls:
checked-ID reservation/retirement is bypassed, no firmware packet timing is
asserted, and production reuse stays prohibited. In-message response_done
rejects duplicates only for that message lifetime; it does not distinguish a
new request after ID reuse. An eventual solution must address this exact
ambiguity, including both RX paths, rather than merely clear the host queue.

## Query-route source check (2026-11-07)

A focused search of pinned SDK include/mcu and mcu sources found channel0x08
and TX-power0x11 used by CmdChannelSwitch and CmdSetTxPowerCtrl with CMD_SET.
The command enum names GET_THERMAL_SENSOR explicitly, but provides no separate
channel/TX-power status query. No corresponding query builder/result layout
was found in those sources. This is a bounded source finding, not proof that
the opaque firmware rejects every possible QUERY. Do not flip set_query or
invent a result layout without a firmware-specific contract. Generic RF/MAC
queries already have distinct reviewed parsers; their existence does not
identify the complete channel/calibration state or establish execution order
for another MCU command.

## Revalidation after optional853 (2026-11-07)

Run42381832296 completed successfully for7bedb0018ac881ff6cfb38f537413638ff716523;
compact target evidence records all three modules and12 channel TU bindings.
The channel/coexistence guards do not resolve the ID budget. Re-executed
check-mcu-rx-direct.py and check-mcu-checked-sequence-retirement.py with
ASan/UBSan on the retained older candidate: both pass, including the deliberately
unprotected same-class replay controls and protected exhausted-ledger refusal.
These tests establish host parser/ledger behavior, not firmware duplicate
lifetime, fresh candidate generation, image integration or device acceptance.

## Exact E2 common-result sequence byte copy (2026-11-07)

Static decoding of exact E2 SHAe897b5ca... locates common result helper106154.
At106164 it loads request byte7 into s4; at1061b0 it stores s4 into output
byte5. Independently checked LBI/SBI opcode/register/offset fields match that
decoding: no4bit mask appears in those instructions. This is stronger than
the host wire declaration alone, but is only this helper's byte-copy path.
Intervening out-of-image calls, input queue ownership and output delivery still
need established contracts. It does not yet prove end-to-end acceptance of
IDs16..255, the E1/ROM loader path, reserved-ID semantics or duplicate lifetime.
No sequence domain change is authorized by this partial evidence alone.

Possible bounded-epoch direction: establish full-byte support for the exact
loaded firmware, then independently bound every checked command in that epoch,
including scan/restore/recovery and runtime. A255-ID pool remains finite; it
cannot replace sustainable reuse if any supported operation can exceed it.
Keep existing retirement and failure behavior while investigating this option.
Exact decoding, raw call candidates and limits are reproduced by
inspect-mt7603-mcu-static.py and its E2 startup JSON report.
