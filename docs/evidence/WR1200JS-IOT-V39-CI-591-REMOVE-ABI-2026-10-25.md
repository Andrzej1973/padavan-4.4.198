# IoT v39 candidate: CI #591 remove-result ABI repair

- Optional GitHub run [#591](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40200096234), commit `c1f43dd`, ended in failure at `Compile isolated merged IoT MT7603 candidate`. This is a candidate compile, not a firmware image or router test.
- The original `iot-merged-driver-probe/build.log` reports `ap/ap_wds.c:1346:5: error: conflicting types for 'WDS_Remove'`; `include/ap_wds.h:126:6` declares the prior `VOID` result. The candidate implementation returns `INT`.
- Source review found a second omitted overlay: `sniffer/sniffer_radiotap.c` defines `INT Monitor_Remove`, while the pinned original uses `VOID`. The candidate headers and wrapper already declare `INT`. Without this overlay the next compile could fail at Monitor as well.
- The versioned candidate now includes `include/ap_wds.h` and `sniffer/sniffer_radiotap.c`; its hash manifest pins 58 overlay paths and 39 original blobs. The WDS preparer and source-directory inventories include both paths.
- `check-remove-result-abi.py` checks eight source/header pairs before and after candidate assembly in the optional CI path. Local positive checks passed on the candidate and assembled tree. The pinned original correctly failed the gate on its `VOID MBSS_Remove` signature.
- Local assembly against the pinned source and prepared tree staged 58 paths with five reviewed text merges. The overlap gate reported five prepared-file modifications, zero missing originals and zero new-file collisions. Python syntax checks and `git diff --check` passed.

These checks do **not** establish MIPS compilation, final image packaging, radio behavior or safe device installation. Next run one optional v39 candidate build only after the normal branch build is terminal; inspect the complete compiler log and monitor report for any further errors.
