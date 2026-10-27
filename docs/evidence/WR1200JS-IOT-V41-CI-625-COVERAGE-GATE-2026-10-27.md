# WR1200JS optional IoT v41 run #625: caller coverage gate

- GitHub Actions run: `40429949035` / firmware #625, commit `2216583bfa812b0d182412267bb5bae3660d28f9`.
- Failed job: `121944962949`, step `Compile isolated merged IoT MT7603 candidate`.
- The original job log ends the candidate's host checks with `Virtual-interface caller coverage changed`: `ap/ap_mbss_inf.c` was expected to contain one direct `VIRTUAL_IF_DOWN`, but v41's callback delegates to `wr_iot_mbss_close_checked`, whose include calls `wr_iot_virtual_down_checked` once. The gate exited 1 before target MIPS compilation. The earlier patch-reject lines in the monitor's bounded excerpt are not the cause of this failure.
- The v40 candidate still has a direct `VIRTUAL_IF_DOWN` in that callback. Its checked-close include exists but is not bound to the callback. Therefore existence of the include alone cannot select the v41 expectation.
- The coverage checker now selects the v41 path only when the callback contains the checked begin/close calls. It requires exactly one callback binding, one checked executor and one checked virtual DOWN call. The v40 direct-call expectation remains intact.
- Local verification: full caller-coverage checker passed on `.iot-local-check/mt7603-v40-repro-20261026` and `.iot-local-check/mt7603-v41-repro-20261026`; two negative mutations (removed callback delegation, removed checked DOWN call) were rejected. `python -m py_compile` and scoped `git diff --check` passed.
- This repairs a CI gate only. #625 produced no v41 MIPS module and proves neither production-image inclusion nor runtime behavior. Repeat one optional v41 run after publication and completion of ordinary same-SHA CI.
