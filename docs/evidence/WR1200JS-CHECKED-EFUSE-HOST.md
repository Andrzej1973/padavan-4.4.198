# Owned EFUSE buffer configuration — host evidence

Package follows 41f93359f18a4da5b59813268ba84d8dd8895b1b. SDK callback
CmdEfuseBufferModeRsp casts the same8-byte EVENT_EXT_CMD_RESULT_T and decodes
LE status. Generator validates callback/layout/enums; command0x21 explicitly
added to reviewed whitelist, independent of channel/TX-power command IDs.
Actual CmdEfusBufferModeSet now uses private owner allocator/initializer/sender
in bootstrap, disables generic callback/storage/retransmission and retains
ordinary SDK route and payload assembly. Both RX paths require command echo,
SET/event0xed/ext0, exact lengths and all4 zero status bytes.

NICReadEEPROMParameters invokes builder subject to CONFIG_ATE and, when
LOAD_FW_ONE_TIME is defined, FWLoad==0. EEPROM type resolves EFUSE or FLASH in
source. This establishes a startup source branch, not effective runtime mode
or permission to bypass LOAD_FW_ONE_TIME bootstrap restrictions.

New cancellation factors existing transport refusal: fresh private message
marks matching config owner failed and frees outside locks. Submission flag
set before transport ownership transfer refuses later cancellation/free.
Invalid EEPROM mode previously reached goto error after allocation with no
free; bootstrap default now cancels instead, without sending malformed data.
Ordinary unsupported-mode SDK behavior was preserved.

GCC ASan/UBSan checks passed full fresh candidate:
- Pure result tests extended to0x21: unaligned, every status bit, echo/event,
  SET/length/null/overflow and unsupported-command refusal.
- Actual EFUSE builder with real SDK structures and injected CmdFillEeprom:
  EFUSE/FLASH paths, firmware status failure, allocation failure and invalid
  EEPROM type; exact alloc/free/message counters and owner failure checked.
- Actual channel builder and all prior MAC/RF owner/readback fixtures.
- Direct/locked checked RX cover all3 commands, status bytes, echo, direction,
  event mismatch and duplicate completion; checked-ID/stale ACK controls and
  bootstrap-result regression retain prior behavior.
- Full manifest inventory and closed outer init gate verified.

EEPROM contents/fill helper, hardware, locks and transport are injected. This
fixture does not validate actual calibration bytes or target/runtime behavior.
No final image or production activation claimed. Temporary generated trees
(~14MB each) and sanitizer binaries auto-removed; unfinished baseline retained.
