# WR1200JS DNS header regression

Status checked on 2026-10-09: the compilation regression is reproduced and the corrected headers pass native and MIPS compilation. The full firmware build remains pending; device behavior is unverified.

## Failure evidence

Full build [101](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37973816375) succeeded. Logs inspected from full builds [102](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37974707886) and [112](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37977707077) show the same failure compiling `services_ex.o`:

- uClibc `ctype.h:72`: `expected identifier or '(' before 'int'` at the `isblank` declaration.
- Padavan `shutils.h:141`: `expected ')' before '==' token` from the existing `isblank(c)` macro.

The DNS configuration header introduced `<ctype.h>` after `rc.h` had already loaded the shared header. The macro expanded inside the libc function declaration. Earlier standalone fixtures loaded the DNS header without the production shared-header order, so their success did not cover this failure.

## Correction and regression checks

[Commit 99ceeb8](https://github.com/Andrzej1973/padavan-4.4.198/commit/99ceeb84d95d18cf6e683d250dce4718b4991ddc) removes the `ctype.h` dependency from the DNS configuration reader. Explicit ASCII whitespace and decimal-digit helpers preserve its configuration grammar. Its fixture defines the pinned shared-header macro before loading the reader.

[ABI run 37979803232](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37979803232) succeeded, including native execution and MIPS compilation of the DNS configuration fixture.

[Commit 6659f1](https://github.com/Andrzej1973/padavan-4.4.198/commit/6659f1f4420adc331cd5ca766994152822a80b61) adds an early check using the actual pinned `services_ex.c` system-include order, `shutils.h`, `defaults.h` and WR1200JS board header. It compiles the DNS/DHCP readiness headers for native and MIPS targets. A negative MIPS fixture must reproduce the original `isblank` collision; failure for another reason does not satisfy that check.

The `Compile IoT readiness headers after actual Padavan shared headers` step in [ABI run 37980231788](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37980231788) passed. The overall run was still in progress at the time of this report.

## Remaining verification

Full build [117](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37979803101), using commit `99ceeb84d95d18cf6e683d250dce4718b4991ddc`, is compiling the firmware. Inspect its actual conclusion and final TRX/config archive before reporting a successful full build. Do not restart a live run because an observation times out.

Header compilation does not prove complete RC linking, ROMFS contents, DNS/DHCP recovery on the router or tunnel reconnection. Those acceptance checks remain required. No router flashing or live configuration changes were performed for this correction.
