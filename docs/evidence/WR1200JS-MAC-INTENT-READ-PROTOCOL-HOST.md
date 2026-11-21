# MAC intent and reviewed multi-register read format — 2026-11-06

The SDK provides CmdMultiPleMacRegAccessRead using EXT_CID / multiple-register
extension 0x0e and the reviewed EXT_EVENT_MULTI_CR_ACCESS 0x0e. Its callback reads
records after 20 payload bytes; one MAC record is type/address/data, 12 more
bytes. MAC_CR is first in its enum (value 0). This supports a MAC readback path
without guessing the EID for separate CMD_ACCESS_REG 0xc2. New generator anchors
verify enum ordering, callback offsets and builder length/direction.

The local MAC decoder requires QUERY, this command/event pair, exactly 32
payload bytes and matching actual/wire lengths. It validates MAC type 0, address
and the full LE value with byte loads. Pure/generated-header ASan/UBSan checks
pass unaligned input, every type/address/value byte mismatch, wrong direction,
extension, length, NULL, wire mismatch and arithmetic overflow.

Before TX, the actual no-response MAC builder now tags address/value. Private
send compares both serialized 8-byte request words, then records the full ticket
and generation in a MAC-specific instance of the existing wire-independent
tuple structure. RF and MAC records are separate. A second unresolved MAC write
cannot overwrite the first. Config finish refuses active/poisoned MAC intent
even if the aggregate unresolved count is zero. There is no clear/retirement
of MAC evidence in this layer.

Fresh generated actual owner/SDK initializer/core gate/builders/private send
tests pass exact MAC intent, duplicate retention, payload/tag mismatch before
hardware, counter inconsistency/poison finish refusal, and the existing RF
write/read retirement path. Hardware/ACK transport and waits are injected.
Complete manifest inventory matches. Temporary candidate (~14MB) and binaries
auto-removed; older unfinished input retained.

The peer82 recipe stages the layer/tests. Target compile and runtime remain
pending. Checked MAC query admission and matching proof retirement still need
wiring; the decoder alone cannot clear the record or unresolved counter. Owner
init/error binding, other protocols, checked-ID budget/epochs, normal promotion
and repeated lifecycle remain required. The outer init refusal stays closed.
