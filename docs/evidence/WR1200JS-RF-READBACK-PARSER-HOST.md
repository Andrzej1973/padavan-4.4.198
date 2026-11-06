# RF readback parser preparation — 2026-11-06

The local decoder matches the SDK RF response representation: three LE words
for WiFiStream, Address and Data, with command/event extension 2 and EXT_EVENT.
It requires QUERY direction, exactly 12 payload bytes, consistent packet/wire
length and exact caller-provided expected stream/address/value. It uses byte
loads, so an unaligned payload and host endianness cannot truncate the result.

The SDK builder expects 12 response bytes and its callback interprets the same
CMD_RF_REG_ACCESS_T structure. This is source evidence for the expected format,
not an observation of actual firmware echo behavior. Generator enum anchors
now verify both RF command and event values before installing the header.

Pure/generated-header ASan/UBSan tests passed a nontrivial 32-bit value at an
unaligned address, mutation of each of 12 stream/address/value bytes, length,
NULL, query, event-extension, wire mismatch and overflow cases. Fresh complete
generation passed the RF protocol anchors, prior owned no-response/synchronous
transport fixture and manifest inventory. Temporary candidate (~14MB) and test
executables were automatically removed.

No checked RF query is admitted by this change. The decoder is not connected
to RX or to the unconfirmed counter. Before wiring it, record the originating
write tuple and full ticket in owned state, bind the query to that record and
copy its result before message destruction. Only a matching checked readback
may resolve that record. Do not clear the aggregate counter on parser success
alone. MAC readback event identity also requires independent source/protocol
evidence; no numeric EID was guessed from the command value.

This local preparation is retained for the next coherent integration package;
it has no target compilation or runtime acceptance yet.
