# Checked channel/TX-power extended completion — host evidence

Source package follows 4c2fa97aeab68f4beb4ccbfa676998e9733e1c48. SDK anchors
require EXT_CMD_CHANNEL_SWITCH=0x08, SET_TX_POWER_CTRL=0x11, extended result
EID0 and8-byte EVENT_EXT_CMD_RESULT_T layout: command echo,3 reserved bytes,
LE status. Only these two commands are admitted; EFUSE not inferred equivalent.

New isolated generator routes actual channel and TX-power builders through
current-task/full-ticket config allocation/send when bootstrap active. Existing
payload assembly and ordinary SDK route retained. Owned initializer disables
retransmission, generic callback and output storage. Sender requires reviewed
command/SET/wait/response8 shape, valid config owner, peer, drained context and
TX-done completion. Both checked RX branches decode exact EID0/event0xed,
command echo and all4 status bytes. No sequence retirement reset or ledger clear.

Passed GCC ASan/UBSan checks against fresh complete candidate:
- Pure decoder: unaligned input, every status bit, wrong echo, direction,
  event and command whitelist, lengths/null/overflow.
- Actual channel builder, SDK initializer/core admission and owner transport:
  success, status/echo mismatch, transport error, late peer drift, TX-done
  timeout. Successful checked completion adds no unresolved MAC/RF effect.
- Actual direct and extracted locked RX: channel and TX-power status bytes,
  echo, direction/event mismatch, duplicate completion.
- Existing MAC/RF intent/readback cycles, noresponse ownership, checked-ID
  exhaustion/stale ACK controls and bootstrap result regression pass.

Host transport/locks/ACK and hardware inputs injected. Actual full TX-power
payload builder is source-routed but not executed by this fixture; its EEPROM
branches and target compilation remain unverified for this package. VOID SDK
return remains; owned allocation/send failure is retained in adapter state.
No production activation, final image or on-device acceptance claimed.

Temporary generated trees (~14MB each) and fixture binaries automatically
removed; retained baseline input remains necessary for unfinished IoT.
