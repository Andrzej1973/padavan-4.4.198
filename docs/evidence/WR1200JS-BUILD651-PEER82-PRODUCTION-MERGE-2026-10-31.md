# Build651 peer82 production merge failure

Run 41235882348 attempt1, commit6b52fcd606498bb3b477bf5bd6789d391358c6ae. Failed job124639489128, step100 Compile isolated merged IoT MT7603 candidate. Original log: assemble-peer-prepared-candidate.py: error: Prepared source overlap/inventory changed (2026-10-31T19:55:36Z). This occurred before candidate Kbuild; no whole-driver target success.

Confirmed root cause: production tools/connected-devices/prepare-radio.py adds two station-query buffer bounds in common/cmm_info.c. The peer candidate also modifies that file. The assembler previously admitted exactly six steering/RSSI overlaps, so the legitimate seventh overlap was rejected. Reproduced the exact rejection locally by applying the actual production preparer to the prepared radios plus pinned httpd source. The three-way cmm_info merge is conflict-free. Diff from the peer candidate consists only of the two production buffer checks; the source hashes and merged output are pinned in PRODUCTION_PINS.

Minimal correction: retain the six-overlap path unchanged; additionally admit exactly those six plus common/cmm_info.c, require exact normalized SHA256 of prepared/candidate/result for the new file, and report actual overlaps/missing paths/collisions on rejection. Unknown overlap sets and input drift remain rejected.

Executed checks: full old six-overlap assembly unchanged byte-for-byte; full production-seven assembly succeeds and cmm_info equals the reviewed merge; deliberately altered prepared cmm_info with the same overlap set is rejected; scratch input restored. Candidate tree /tmp/wr-abi599-full.vEmGGs/merge-production-seven. YAML and Bash checks cover the additional local merged-task macro evidence wiring; actual target execution remains pending.

Monitor comparison: monitor run41236498319 artifact agent-build-error-41236498319 identifies build651, failed job and step correctly, but its first256KiB excerpt omits the causal assembler error and includes earlier nonfatal patch messages. Current branch build_monitor.nim already has bounded last16MiB/latest60-lines handling and a late-error regression; that change is not deployed in the trusted main-branch monitor. No duplicate speculative parser change made. Default-branch deployment remains outstanding; logs are untrusted data.

No production installation, image/device acceptance, router writes, service restart or reboot. Next: publish this coherent fix, reuse its automatic CI and run one isolated peer82 target check on the exact new revision when no duplicate firmware run is active.
