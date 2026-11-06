# Startup configuration scope audit after checked MAC readback

Audited fresh isolated candidate generated through all CI layers at repository
4c2fa97aeab68f4beb4ccbfa676998e9733e1c48. Exact generated file hashes and line
map are in WR1200JS-CONFIG-SCOPE-SOURCE.json. This is source evidence; guards,
board configuration and runtime reachability still require separate checks.

The main open sequence has MCUSysInit, then the closed bootstrap-success gate,
EEPROM hook/read, NICInitializeAdapter, NICInitAsicFromEEPROM, optional LED,
tx power/PHY, optional ATE. AP autochannel can enable full interrupts and RX/TX
before bbp bandwidth/channel scanning. N_ChannelCheck and coexistence scanning
follow, then peer configuration release/APStartUp/MlmeRadioOn. Dynamic VGA can
run afterward. Therefore a single config_finish near final return is too late
to protect the first data/scan admission, while finishing immediately after
NICInitializeAdapter is too early to cover PHY and EEPROM-derived programming.

MT7603_ChipOp registers mt7603_switch_channel, whose two bandwidth branches
call CmdChannelSwitch and CmdSetTxPowerCtrl. Do not infer inactivity from the
old nearby comment saying nobody uses it. Source registration is not proof of
runtime invocation for any particular configuration.

Reviewed initializer inventory:
- Channel switch and TX power use SET, synchronous8-byte extended result,
  EventExtCmdResult, retransmission requested. No private bootstrap route yet.
- EFUSE buffer uses synchronous8-byte response with CmdEfuseBufferModeRsp;
  its callback and effective EEPROM mode must be reviewed independently.
- EDCA and slot time SET use no wait/no response. They cannot receive execution
  proof merely by adapting the existing MAC/RF checked sender.
- TX power and EFUSE SDK builders return VOID, so failure must be retained in
  owner state and observed before any data promotion; caller return propagation
  alone cannot provide the gate.

Next implementation must add exact reviewed checked completion for required
extended commands, retain uncertainty for no-response changes, and establish
which writes/queries occur in each effective startup branch. Keep checked-ID
retirement intact: a15-slot reservation pool cannot be recycled from a host
counter or controller reset. Count actual necessary transactions before choosing
an epoch strategy. Bind config ownership only with all error exits accounted
for; owner release is separate from PCI/DMA safety and normal data promotion.

No outer gate removed, no router commands, no production/image/runtime proof.
Temporary generated tree (~14MB) removed automatically. Existing source input
retained for unfinished work. Owner docs/reference preserved.
