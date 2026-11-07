# Serial-owned checked OFF candidate

Added final isolated layer binding ASIC checked OFF -> ticket-aware builder
-> owned sender entry -> existing checked private transport. Admission checks
CLOSE serial/epoch/stage, closes normal sends, waits outside locks, revalidates
after drain, takes OFF lease under transition->sender lock order, finishes
OFF from returned checked status and wakes waiters before final unlock.
Rejects retransmission/non-response modes and consumes only private refusal
messages. Never reads msg after transport; no sequence/epoch reset or reopen.
Default one-time-firmware refusal remains. Ordinary callbacks remain unbound.
Generated source hashes updated; CI executes the installed fragment host test
and requires a defined nonempty owned-OFF symbol in the MIPS module.
ASan/UBSan fixture passed success with an existing sender, duplicate OFF,
transport failure/uncertainty, undrained sender, epoch change during wait,
wrong serial, atomic/IRQ-disabled context and retransmit refusal. Transport
frees msg in the fixture to check post-transfer lifetime. Transformation on
preserved source files, manifest digests and duplicate rejection also pass.
This is mocked transport/host control-flow evidence, not full-chain target or
firmware ACK freshness, DMA/IRQ drain, safe reopen or runtime acceptance.
Scratch removed; old phase inputs and owner references retained. No router use.
742 reload artifact verified as below; whole workflow still queued at check.
