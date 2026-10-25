# IoT v39 candidate: #593 main-open header failure

Optional GitHub [build #593](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40203910623) on `ff6f0b1` completed with failure at `Compile isolated merged IoT MT7603 candidate`. Its ordinary firmware image and Band Steering ABI checks had already passed on the same commit in runs `40202508394` and `40202508377`.

The GitHub monitor artifact identified the failed step but its old `main` extractor scanned only the first 256 KiB and showed unrelated early messages. The authoritative `iot-merged-driver-probe/build.log` says:

```text
os/linux/rt_main_dev.c:184:3: error: implicit declaration of function 'wr_iot_main_open_reserve' [-Werror=implicit-function-declaration]
```

The helper exists as a static inline in the candidate's `include/virtual-open-claim.h`. `rt_main_dev.c` did not include that header; it now does. The candidate remains 58 overlay files and 39 pinned original blobs. Its manifest hash was regenerated against the reviewed source. Local Python syntax, manifest-gated assembly into the prepared source (five reviewed merges), eight-pair remove-result ABI check and readback of the new include passed. The locally updated Nim monitor found the exact #593 compiler line on a read-only recheck; no further parser change is justified for this case.

This is a source repair, not proof of successful MIPS compilation. The v39 candidate is still isolated from the production firmware image and has not been exercised on the router. Run one optional v39 compile after the normal branch build on the repair commit finishes; inspect its complete log before advancing.
