# Optional 742: full reload target evidence

Optional 41858780303 on 8dd0568b has uploaded driver artifact 13340566215.
Full workflow still queued with build job 126674659484 in progress and final
jobs queued; do not call the whole run successful until terminal confirmation.
Independently verified full reload MIPS module 5574296 bytes SHA256
1c7a7b590e373703ca7699f229beef55e8f817d27beea46f770082a41179e30f,
baseline report/config binding, four effective MCU/RX/ASIC/task macro inventories
and source hashes against candidate manifest. LOAD_FW_ONE_TIME false in all
four; checked-off symbol 1096 bytes, not known refusal. Production/epoch/
shutdown/runtime remain false. Compact reports in WR1200JS-BUILD742 (67761
bytes before README); ZIP/modules stayed in memory, no scratch retained or
removed (0 disk bytes reclaimed). Preserve unfinished inputs/owner material.

Source review: sender_off_begin/finish exist in the owner model/tests but have
no generated production-path caller. sender_close_drain likewise is not yet
bound to checked radio OFF. Ordinary wrapper refuses all sends once closed;
radio-only checked transport must not simply be widened to restart commands.
Next implement and verify the ticket/serial-bound owned OFF path with closed
normal admission, drained existing senders, IRQ/RX alive through checked ACK,
private transport ownership and off_finish before later DMA/IRQ retirement.
Do not clear quarantine or reopen a poisoned owner based on this compilation.
Firmware restart additionally needs separate response format/status and replay
policy; current callback is log-only. No router action or ordinary ndo binding.
