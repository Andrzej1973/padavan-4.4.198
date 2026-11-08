# WR1200JS over-the-air ACK timing investigation

2026-11-08. Repository c261d5d953c53ca894e7e1c5a67ec65666cc6a73.
Board is YOUHUA WR1200JS, not ASUS. Driver inspected: pinned vendor mt76x3
c25283e915a2a00a763774dd255b14aff997285e, MT7603 PCI/MT_MAC.
Status: hypothesis unconfirmed, no timing modification applied.
This is separate from MCU command ACK sequence exhaustion and beacon TxS ownership.

## Exact source locations

Paths below are relative to the pinned vendor driver root. Actual inspection
input: /home/andrzej/padavan-build/legacy-materials/iot-pinned-mt76x3-c25283e/mt76x3.

- hw_ctrl/cmm_asic_mt.c:1854 AsicSetSlotTime: slot9/20 us, band-specific
  SIFS_TIME_24G/5G; calls CmdSlotTimeSet. Altering this affects shared radio timing,
  not just the IoT BSS. It is not an ACK receive-timeout setter.
- mcu/andes_mt.c:3903 CmdSlotTimeSet: actual firmware command construction.
  Preserve command protocol and checked-result/ownership layers in candidate.
- include/mac/mac_mt/wf_tmac.h: TMAC_ICR has named SIFS/SLOT/RIFS/EIFS fields.
  These do not establish an ACK-timeout field or safe replacement value.
- hw_ctrl/cmm_asic.c:1493 legacy AsicSetSlotTime uses BKOFF_SLOT_CFG;
  include/mac/mac_ral/rtmp_mac.h:747 defines0x1104. Do not transplant this
  register write into the selected MT_MAC path.
- common/cmm_profile.c:1399 parses AckPolicy into CommonCfg.AckPolicy[4].
  common/cmm_data.c:2280/2288 consumes it for access categories. It is not a
  per-IoT timeout; disabling normal ACK removes reliability rather than fixing it.
- common/cmm_info.c:Set_HtBaWinSize_Proc (around4175), Set_HtAutoBa_Proc
  (around4256): RX BA window and automatic BA policy. These are separate from
  immediate ACK timing; do not change globally without BA-specific evidence.
- chips/mt7603.c:271 modifies TMAC_TRCR CCA selection bits for throughput;
  hw_ctrl/cmm_asic_mt.c:AsicSetRDG modifies I2T_CHK_EN. Neither is demonstrated
  here to be an ACK-timeout control. Preserve unrelated bits.
- common/cmm_usb_io.c EXP_ACK_TIME adjustments are USB-path evidence, not proof
  of a supported PCI MT7603 ACK-timeout setting.

## Implementation decision

No unconditional timeout/SIFS/slot patch is justified by the supplied symptoms.
Low-power operation is not itself evidence of late over-the-air ACKs. Missing
ACK can instead reflect sleeping STA, loss/interference, retries, rate selection,
power-save buffering or aggregation interoperability. Establish direction first:
AP waiting for STA ACK differs from AP ACKing STA uplink. Host MCU ACK timeout
is a third, unrelated mechanism.

Before introducing a register patch obtain:
1. Reproduction on ordinary Main/Guest versus IoT with same client/channel/key
   and loaded firmware identity, uptime, disconnect reason and retry statistics.
2. Monitor capture preserving control frames and reliable timestamps: AP unicast,
   retransmissions, client ACK/BA, PHY rate and power-management indication.
   Ordinary host packet timestamps do not establish SIFS-scale on-air timing.
3. Controlled single-variable experiments: client power save enabled/disabled,
   HT aggregation on/off only if the driver supports scoped selection, HT20,
   fixed test placement. Record results without declaring a fix from one trial.
4. Named MT7603 ACK-timeout register/mask/unit and ownership/writer audit, or
   documented firmware command. Upstream mt76 is comparison, not permission to
   use its register definitions blindly in the vendor stack.

## Precise patch/compile/test route once timing fault is confirmed

Implement an isolated transformation after prepare-driver-api.py in
 tools/iot/ci-compile-merged-candidate.sh, with exact source anchors and manifest
hash updates. Do not edit the preserved pinned input or bypass stale-ACK guards.
For an ACK-timeout-only experiment, add a board/chip-gated helper at the actual
MT7603 timing initialization writer, using a validated mask/units and bounded
value. Use read-modify-write/readback and retain original unrelated bits. Do
not implement this using BKOFF_SLOT_CFG, SIFS or AckPolicy as a substitute.

Test extracted actual C helper for mask preservation, invalid chip/value,
readback failure and reset/reinitialization behavior. Lightweight checks locally;
full kernel/module/firmware only on GitHub. Publish one coherent package, wait
for its standard success, dispatch optional boards=wr1200js,
run_candidate_checks=true,candidate_scope=iot,iot_candidate_variant=peer82,
verification_revision=<exact40SHA>; reuse equivalent runs, no duplicates.
Verify source SHA, effective config, MIPS module, final image separately.

Physical testing requires separate authorization. Use A/B stock versus experiment,
Main/Guest/IoT concurrent traffic, sleep/wake cycles, DHCP/DNS/internet,
IPv4/IPv6 isolation, restart/reboot, ACK/retry/disconnect metrics and throughput.
Accept only measured improvement without regression. Keep original image and
recovery access; do not flash or restart as part of source-only investigation.
