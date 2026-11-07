# IoT main VERIFY checked rollback — isolated v21, 2026-10-28

The isolated v20 chain can finish main virtual open and then fail its MT7603 radio-readiness VERIFY. At that point Linux will not call `ndo_stop` for the failed `ndo_open`, so the driver must not silently drop the acquired virtual reference or module pin. v20 retained them but did not start recovery.

`tools/iot/prepare-main-verify-rollback-candidate.py` produced `.iot-local-check/mt7603-main-recovery-steering-rollback-v21-20261028` from the reviewed v20 tree. It verifies the input hashes before copying. The v21 composition has the same 67 files; only `os/linux/rt_main_dev.c` changed. All 67 output hashes match its composition manifest. `production_installed=false`.

On failed VERIFY, the staged `MainVirtualIF_open` now attempts the existing checked close while `ndo_open` still holds RTNL. It requires the same main generation, records the one-time vendor preclose attempt, and releases the module pin only after `wr_iot_main_close_continue_checked` reports a complete close. Any rejected or incomplete stage retains the owner and pin. HNAT registration and queue wake remain after successful VERIFY. This reduces the ordinary failed-VERIFY leak path; it does not implement a recovery drain for a partial close.

Checks actually run on Windows:

- `python -m py_compile` for the preparer and two source checkers: pass.
- `python tools/iot/check-main-readiness-verify-candidate.py <v21>`: pass, including conditional checked rollback ordering.
- `python tools/iot/check-virtual-if-call-coverage.py <v21>`: pass. The same broad gate still accepts v20.
- `gcc -std=c11 -Wall -Wextra -Werror -I <v21>/include -I tools/iot tools/iot/check-main-verify-recovery.c ...` and executable: pass. This models failed VERIFY, close admission, retained owner on rejected scheduling, and joined retry; it does not execute the actual wrapper.
- `gcc -std=c11 -Wall -Wextra -Werror -DWR_IOT_V40 -I <v21>/include -I tools/iot tools/iot/check-mbss-post-open.c ...` and executable: pass for guest/IoT, readback, count, reset and partial-open ownership.
- `gcc -std=c11 -Wall -Wextra -Werror -I <v21>/include -I tools/iot tools/iot/check-virtual-open-claim.c ...` and executable: pass.
- `python tools/iot/prepare-main-verify-rollback-check.py <v21> .iot-local-check/main-verify-rollback-v21.c`, then `gcc -std=c11 -Wall -Wextra -Werror -I <v21>/include -I tools/iot .iot-local-check/main-verify-rollback-v21.c ...` and executable: pass. This extracts the actual `MainVirtualIF_open` body and injects complete close, rejected close admission, failed preclose and failed continuation. It confirms the wrapper releases the pin only after complete close, retains it otherwise, and never wakes the queue after VERIFY failure. VERIFY and checked-close helper implementations are mocked; this does not prove their real hardware behavior.
- `git diff --check`: pass; Git emitted only line-ending conversion warnings.

An initial MBSS host compilation without `-DWR_IOT_V40` failed on unused mock publishers. That selects the old fixture include; rerunning with the intended v40 define passed. It was not a candidate-source failure.

Open gates: an incomplete checked close still retains ownership without a bound worker; the callback lacks a proven RTNL/netdev/adapter lifetime and PCI-remove join protocol. The extracted-wrapper fixture does not execute the real VERIFY or checked-close implementations. There is no MIPS target compilation, finished firmware image, RF-frame observation, or router runtime proof for v21. Do not install or package it until those gates are closed.
