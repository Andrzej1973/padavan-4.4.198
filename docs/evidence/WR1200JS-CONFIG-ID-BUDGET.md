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
does not satisfy the port objective. EDCA/slot execution proof remains a
separate unresolved requirement.

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
