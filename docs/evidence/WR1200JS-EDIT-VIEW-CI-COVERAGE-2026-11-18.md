# IoT edit/view CI coverage — 2026-11-18

The ABI workflow previously ran the physical-stop suite but did not invoke
`check-config-edit-suite.py`. Successful ABI checks therefore did not establish
the new private view, revision lease or typed configuration edit contracts.

A dedicated step now runs that suite using the existing pinned SDK checkout:
`vipshmily/padavan-4.4@c25283e915a2a00a763774dd255b14aff997285e`.
It supplies the actual `nvram_linux.c` to capability/staging checks and the
actual HTTP source directory to authenticated route preparation checks.
The same suite also runs the isolated Classic ROMFS staging check.
No new download, target compilation or router operation is added by this step.

Companion Classic configuration hardening bounds returned public fields,
refuses inconsistent absent configurations and requires a fresh read after
110 seconds or browser clock regression. The existing RC monotonic lease
remains authoritative; browser timing does not extend it or prove acceptance.

The combined host suite completed with exit0 before publication, including
the added Classic ROMFS staging check. Workflow YAML parsing and whitespace
checks also passed. Its GCC/ASan/UBSan,
fork/socket and simulated DOM checks do not establish MIPS/image/browser or
physical acceptance. The new workflow step itself still needs a GitHub run.
Optional1377 verifies the preceding published revision, not these edits.

Baseline ABI930 completed in approximately 10m19s, with its physical-stop step
taking 5m54s. The existing 20-minute job budget is retained; new measured CI
duration must be checked rather than assuming unlimited additional headroom.
