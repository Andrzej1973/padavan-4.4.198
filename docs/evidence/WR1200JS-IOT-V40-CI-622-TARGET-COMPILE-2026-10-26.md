# WR1200JS IoT v40: isolated target compile in build #622

GitHub Actions run `40387415111` (build #622) completed successfully on
published commit `b2ec88960a545e67509d5e64b9f78ef580311054`.
It selected `boards=wr1200js`, `run_candidate_checks=true`,
`candidate_scope=iot`, `iot_candidate_variant=v40`. The prior #620 had stopped
before compilation because IoT-only scope lacked the isolated kernel tree;
#622 confirms that the repaired preparation path reaches and completes the
candidate build.

The downloaded `iot-merged-driver-probe` artifact (`12682611244`) contains
`target-compile-result.json`, source/overlap manifests, the build log, capacity
report and `mt76x3_ap.ko`. The result names pinned source
`c25283e915a2a00a763774dd255b14aff997285e` and reports variant `v40`,
`target_compiled=true`, `production_installed=false`,
`runtime_verified=false`. The module is 5,212,832 bytes; independent SHA-256
of the downloaded file matches the report:
`8e1543a67bb223755bd174148f8a02a566d762d75ba91a8ea0ce9388b9b0f455`.
Its ELF header is ELF32 little-endian, relocatable MIPS32r2/O32. The symbol
table contains `wr_iot_mbss_begin_close`, `wr_iot_mbss_close_checked`,
`wr_iot_virtual_down_checked` and `wr_iot_mt_radio_off_checked`.

The merged-source manifest records 58 overlay files and one resolved text
conflict in `common/rtmp_init.c`; no production installation is claimed.
The capacity report still says `runtime_verified=false`. The build log has
one nonfatal `modpost` section-mismatch warning without expanded detail.

This is **isolated candidate target-compilation evidence only**. The ordinary
firmware image was built before the optional candidate step and does not
contain this module. Source reachability, recovery ownership, BSS-close
ordering, PCI remove lifetime, IoT isolation, WebUI Apply and physical-router
operation remain open release gates. No router change occurred.
