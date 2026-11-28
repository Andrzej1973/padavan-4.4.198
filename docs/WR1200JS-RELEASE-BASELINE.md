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
  is the image verification run for that revision.

See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for hashes and test scope.

## Acceptance evidence

For each candidate, bind the build and artifact to the exact source commit,
toolchain and effective configuration. Inspect the final TRX size and SHA-256,
ROMFS feature inventory and the release gates. CI success and image inspection
do not establish physical router operation.

Physical WR1200JS acceptance remains NOT RUN for any image that has not been
installed and tested on the device. Do not mark an image READY FOR RELEASE
while required IPv6 routing/cleanup, current-HEAD CI, image composition or
critical security findings remain unresolved.
