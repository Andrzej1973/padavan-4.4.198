# EDCA and slot-time request journaling — host evidence

Source package follows `04bf80d392f7c79d1aea5ecd2bf0ec69f4318e71`.
The SDK declares EDCA command `0x27`, slot-time command `0x28`, four maximum
EDCA AC records, and no response/callback/storage for either command. Their
successful TX completion cannot prove firmware execution.

The new isolated stage records exact serialized no-response data plus the full
peer/radio/close ticket before TX. EDCA is rejected before allocation/copy when
its count is zero or greater than four. Record validation requires an exact
four-byte header, unique AC identifiers 0..3, nonzero supported valid bits,
and the expected byte length. Slot-time requires its exact eight-byte shape
with reserved bytes zero. One pending record of each kind refuses overwrite;
overflow is rejected by the existing unresolved-effects counter.

Configuration finish now refuses while either timing journal is active or
poisoned. The stage deliberately provides no clearing/readback API. Existing
source-side WMM register reads lack an established ordering and execution
receipt for this firmware command, so they are not used as a proof.

Call-site audit found EDCA changes from WMM parameter updates and AP EDCA
application, and slot-time changes after AP capability/ERP decisions. Those
paths can also run while the AP is operational, so an initialization-only
receipt or a host reset must not be reused for a later runtime command. The
current bootstrap gate remains closed and therefore does not claim these live
paths are admitted.

GCC ASan/UBSan host checks passed actual SDK EDCA and slot-time builders,
request byte layouts, full tickets, duplicate/timeout/transport retention,
invalid count/AC/valid-bit/header, unresolved-counter overflow and owner finish
refusal. The actual configuration-owner fixture also passes with the new
records. RX, checked-ID and prior MAC/RF/EFUSE checks retain their behavior.
Locks, firmware delivery and EEPROM state are injected. No target image or
device-runtime claim is made. Temporary generated candidates and test binaries
are removed automatically; the retained baseline input remains required.
