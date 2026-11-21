# WR1200JS current verification checkpoint — 2026-11-18

This checkpoint separates evidence scopes; it does not promote a release.
Current published driver source is 7334562620fb6c9961a72bc5e8ce9de01920bc16.

| Requirement | Evidence / remaining action |
| --- | --- |
| Queued EAPOL association generation | Implemented in isolated peer82: persistent WCID generations, queued stamp, execution validation, no wrap; native enqueue host tests pass. Latest MAC-only ambiguity refusal and stale-slot publication fix need exact-revision optional target evidence. |
| ra2 requested/periodic GTK versus association mutations | Complete source arbitration composed; host fixtures execute native callback/request with retained peers. Optional1412 for730af649 is compiling; this checkpoint does not claim its result. |
| Optional direct key ioctl | Failed-copy refusal composed. Lifetime/BSS lookup and native-body factoring prepared but unbound. HOSTAPD target reachability awaits per-TU macro evidence from optional1413 or later. Do not enable the dormant feature based on host tests. |
| Existing target/image evidence | Optional1406 a59d9f1f module and selected TRX files independently audited. Image SHA2561f253cf79325bb240af06537972e091f60819942a43dde88def246368f1abe4e,14550238bytes; partition remainder1637154bytes. This predates complete arbitration and latest generation fixes. |
| Saved versus applied configuration | package-candidate-pair.py still requires configuration_flash_bound=false and configuration_loaded_promotion_bound=false. Complete owned saved/loaded integration before promotion; preserve current settings. |
| Main image | Isolated packaging exists; production installation remains false. Do not flip readiness flags to substitute for integration. |
| ACK and PCI/DMA/IRQ | Preserve current protections and established resource owners. Host/source/target evidence does not establish physical completion or safe device acceptance. |
| Modern/Band Steering/Zapret2 | Owner resumed Hybrid Modern settings/apply work on 2026-11-20; IoT remains first. Modern IoT host candidate reaches native HTTP handlers and actual mailbox submission/claim; RC persistence, target/image integration and device acceptance remain open. Preserve Band Steering. |
| Final release | Four HybridModern variants (Classic present/absent × CAKE present/absent), image/config/release gates and separately authorized device acceptance remain required before Mi Mini. |

CI snapshot: standard1409,1410,1411,1415 succeeded. ABI948–950 succeeded;
ABI951 was live at inspection. Standard1416/1417 and ABI952/953 wait.
Optional1412/44383452431 is live;1413/44383458093 and1414/44383465494 wait.
Optional1418/44387982878 queued exactc6544dd5 after standard1415 success.
These are a timestamped snapshot, not a standing current-status claim.

Next decisive actions: triage any first actionable optional failure through its
monitor/original step; obtain exact prepared-source/module/image evidence for
complete arbitration; use actual key-writer TU macros to bound optional ioctl
work; finish owned saved/loaded configuration and main-image integration.
No router-side change or runtime acceptance is authorized by this checkpoint.
