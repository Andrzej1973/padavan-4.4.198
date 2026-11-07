# WDS operation ownership: publication checkpoint

The owner authorized publication of appropriate local work on 2026-10-29.
The previous published checkpoint is `88938ff` on
`codex/wr1200js-service-webui`. This checkpoint adds only the independently
testable, project-authored WDS operation helper and its host test:

- `tools/iot/wds-peer-operation.h`
- `tools/iot/check-wds-peer-operation.c`

The helper checks device identity, registration generation, active-operation
count, removal admission and counter overflow. All access requires the adapter
transition lock. Initialization is only valid for a fresh/quiescent registration.
It is not an adapter/netdev pin, a unique operation token, or evidence of
callback, DMA or TxS quiescence. A duplicate leave while another operation is
active cannot be detected by this counter alone; callers need structured cleanup.

## Verification actually performed

Windows host GCC compiled the test with `-std=c11 -O2 -Wall -Wextra -Werror`;
the executable exited successfully. `git diff --check` passed before staging.
This is a sequential host test, not a MIPS driver build or concurrency proof.

## Work intentionally still local

The source-transformation candidates, broader modified files, accumulated status
documents and downloaded/generated driver source trees were not included in
this publication. Their current detailed continuation is in the local
`PROJECT_STATUS.md` and `CODEX_HANDOFF.md`.

The next unresolved WDS step is a temporary age-out ownership reservation across
peer deletion and WDS-slot cleanup, with exact registration/slot identity and
close/reset exclusion. The slot-allocation gate alone does not close this race.
Final callback/queue/DMA/TxS retirement and retained-netdev completion remain
open. No production backend, image acceptance or on-device acceptance follows
from this checkpoint. No router changes or full firmware build were performed.
