# WR1200JS iPerf3 image lifecycle gate — 2026-10-21

The existing `overlay/padavan-4.4/ports/iperf3/verify-image.py` checked the
status UI, HTTP status handler, help text and translations. It did not assert
that the selected image contained an executable target iPerf3 server, its
lifecycle helper, or the compiled Apply route.

The verifier now requires a little-endian MIPS ELF `/usr/bin/iperf3`, an
executable `/usr/bin/iperf3.sh`, the helper path in the final RC binary, the
factory-off default, the `iperf3_enable` restart field/event in prepared HTTP
source, and the restart dispatch string in the final HTTPD binary. Existing
UI/status/translation checks remain in place.

The WR1200JS workflow also runs the existing package-closure verifier against
`usr/bin/iperf3` in the final ROMFS. It checks the executable's ELF interpreter
and recursively resolves its linked libraries from the same image. The
diagnostic artifacts are `iperf3-image-checks.json` and
`iperf3-elf-closure.json`.

Python syntax and `git diff --check` passed locally. A local Padavan source
fixture contains the expected RC helper calls, factory-off default and HTTP
field/event registration. These are source checks only. The expanded verifier
and dependency-closure gate have not run against a new final image. An authenticated browser Apply,
start/stop behavior, a bounded LAN client test, throughput and reboot
persistence remain unverified on the router. No router state was changed.
