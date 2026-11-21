# Build #498 KVR image failure — 2026-10-20

#497 (run 39450409614, head 6cb5f3d) succeeded. #498 (run
39451630662, head 04cad5b) failed after firmware compilation/image creation
at verify-wifi-kvr-image.py. Band Steering ABI #473 succeeded independently.
The later missing EoIP report is consequential: the preceding image gate
aborted that step before the EoIP evidence could be generated.

Original job 118727741426 log was downloaded and processed with local
build_log.exe, then checked against the original. KVR artifact 12279498338
and failed-firmware evidence 12278963970 confirm all three MT7603E K/R/WNM
options OFF in both the prepared board config and effective kernel config;
all eight required executable symbols are missing from linked/shipped
modules. The generator, HTTP controls/registration and defaults passed.
Do not weaken the gate or call this a compiler failure.

Root cause: 04cad5b changed the repository overlay board template, but the
workflow does not wholesale copy that template into the donor build tree.
It selectively copies board.h/partitions and merges USB settings into the
donor board config. The approved KVR values consequently never reached it.

Fix: prepare-wifi-kvr-board.py transfers ONLY the three approved KVR options
from the repository template into the actual WR1200JS build-tree config.
It requires the expected radio selection, unique target options and approved
enabled values. The workflow calls it before compilation. Existing final
config/module/WebUI verification remains mandatory and unchanged.

Local check used the exact downloaded #498 board config: only three lines
changed, repeat transformation is stable, and six missing/duplicate selector
variants reject. A new complete CI/image result is still required; router
client k/v/r and FT interoperability remain unverified. No router writes.
No IoT integration was added to this build change; queued Classic work keeps
its approved delivery order.

Original log SHA256: `e0fff3da007dabce6078b553bdfe2347854f8a5ad94eff1cce62603c3d1e64b8`
