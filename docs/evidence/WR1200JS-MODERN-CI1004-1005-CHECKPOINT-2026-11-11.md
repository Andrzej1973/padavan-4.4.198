# Scoped target/image checkpoint

##1004: isolated atomic Guest route

Run42999753636 requested/verified1b4c4740ba0e7143757aae0f8d04619604ca5fc7.
Actual linked HTTP ELF32LE MIPS358356B SHA256
917c0e984937c484acba886b191e1380c41c790c7196be7f4804427ae1e674a3
matches compile report. Exact Git headers, including Guest planner/batch client,
reconstructed and hash checked. Actual kernel object and client/planner probe
also hash-match reports; kernel/client ABI report agrees. Production source/
binary hashes before/after remain identical. Candidate APIs and handler are
compiled only in isolation, not installed into production firmware.

##1005: test image with accepted page04

Run43002411476 verifiedc4895bec3a73e263d87977a481e9c5fe2cf2c0f3. Independently
downloaded actual test TRX13100553B SHA256
6269f5707b64cbfd191b1b61979d7ff3d397e5d624bfe2ffe3e7232f809874b5.
Checked uImage header/payload CRCs, declared length/product/size and embedded
IoT/HWNAT DTB policy using unchanged verifier. Found exactly one valid SquashFS.
Prepared all7 Modern assets anew using exact Git production generator/assets;
selected files extracted from actual image match bytes and regular-file modes.
Only minimal dummy HTTP/Makefile anchors were supplied for asset generation:
this reconstructs assets, not the full compiled production HTTP source closure.
Compact structure/file hashes in companion IMAGE1005 JSON.

These are build/image checks for a test firmware, not final release, boot,
operational IoT or physical client acceptance. CAKE, complete feature/runtime
and settings migration acceptance are not newly established by this selected
Modern-content check. Classic retained; final paired release comparison pending.

Cleanup: actual ZIP/ELFs for1004 read in memory.1005 owned image/preparation/
selected-extraction scratch13651905B auto-removed, absence asserted. No full
ROMFS extraction or retained firmware/archive. Source, fixtures and user data
preserved. On source review and absence of matching optional in latest20 runs,
queued exactc4895be optional43005464137; dispatchhead2beb63b differs from build
source. ABI43004583856 separately verifies2beb63b OFF-owner correction.
