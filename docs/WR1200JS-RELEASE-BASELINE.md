# WR1200JS release baseline

Owner decision, 2026-11-24, reaffirmed for the technical audit on 2026-11-25.
This file is the current release-policy source for WR1200JS. Older planning
notes remain in the repository as history and are superseded where they differ
from this baseline.

## Standard image

- Classic WebUI.
- Main and Guest Wi-Fi.
- Isolated IoT Wi-Fi and its `ra2` payload excluded.
- CAKE/SQM excluded.
- Existing production services retained according to the board's supported
  kernel, backend, configuration and image contents.
- Factory defaults do not enable experimental services or overwrite saved
  user selections.

The default Standard workflow input is `sqm_profile=excluded` and does not run
experimental candidate checks. `candidate_scope=iot` only selects an isolated
candidate compilation when `run_candidate_checks=true`; it does not add IoT to
the Standard image.

## Experimental candidates

Isolated IoT/MT7603 work and the optional SQM image remain development
candidates. The SQM candidate is selected explicitly with `sqm_profile=profile`
and keeps runtime `sqm_enable=0` by default. Neither candidate is part of the
Standard release image.

## Verified CI candidates

- [Standard #1543](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46121413500)
  and [SQM #1545](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46127361867)
  each produced matching TRX SHA-256 values across two successful attempts on
  d93e0ac8. The SQM image passed the factory-OFF check.
- [Service CI](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46131574569)
  passed on 4c95cef6. [Standard #1546](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46131780143)
  passed image verification on that revision. Its 13,065,507-byte TRX
  leaves 3,121,885 bytes in Firmware. The linked image and final-content
  reports confirm both CRCs, declared length, Classic-only, IoT and SQM
  exclusion, and the exact VPN service script from that revision.
- [SQM #1547](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/46133859566)
  passed on the same 4c95cef6 revision. The 13,100,191-byte TRX leaves
  3,087,201 bytes in Firmware. TRX, ROMFS and CAKE reports agree on SHA-256
  `66b91cc43c458c486d3ec0b07e59c62625cdd1b3e64662fdda1999f435e24dec`.
  Classic-only, IoT exclusion and SQM factory OFF passed, and the VPN
  service digest matches Standard #1546. The reproducibility result from
  SQM #1545 applies to d93e0ac8.

See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for hashes and test scope.

The matching hashes on d93e0ac8 establish reproducibility for those CI inputs.
The two profiles on 4c95cef6 have one verified build each.
The workflow still installs runner packages and can fetch missing pinned
source archives. A full network-disabled build has yet to be verified.
See [sources.lock.json](../sources.lock.json) for source pins and
the recorded self-contained build status.

## Acceptance evidence

For each candidate, bind the build and artifact to the exact source commit,
toolchain and effective configuration. Inspect the final TRX size and SHA-256,
ROMFS feature inventory and the release gates. CI success and image inspection
do not establish physical router operation.

Physical WR1200JS acceptance remains NOT RUN for any image that has not been
installed and tested on the device. Do not mark an image READY FOR RELEASE
while required IPv6 routing/cleanup, current-HEAD CI, image composition or
critical security findings remain unresolved.
