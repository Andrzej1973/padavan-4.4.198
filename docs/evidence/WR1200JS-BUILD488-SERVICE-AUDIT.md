# WR1200JS build 488 — selected service/WebUI image checkpoint

Date: 2026-10-19. GitHub Actions run
[`39275709312`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39275709312)
completed successfully. The target image was
`WR1200JS_4.4.198.9-488.trx` (12,616,562 bytes; SHA-256
`9a0b641b4b7c308eda7f25321f41321ce161eb4b8db4cb0e6373dac28287515f`).
Source head: `b99d9cd19ec5aa96d550ddf547bc32d92d505d03`; reusable workflow
merge SHA: `a600659e21b63bd8153d51833d2278e203bd4811`.

This is CI and final-image evidence only. The image was not installed on the
router as part of this checkpoint.

## Relevant checks reported by the workflow

- Final-ROMFS unified service navigation verifier passed for routes, pages,
  and EN/UK/RU labels. Service pages point back to
  `/Advanced_Services_Content.asp`.
- Selected-image BusyBox service-map precompile gate passed. This is a
  selector/image gate, not a full lifecycle and error-recovery audit of every
  enabled service.
- EoIP is disabled in `configs.build/wr1200js.config`. Artifact
  `eoip-image-checks` (`12199565711`) recorded
  `PASS disabled EoIP selector and final ROMFS absence; runtime unverified`.
  Selected-image integrity, disabled-image absence, and rejection cases also
  passed. EoIP is therefore correctly omitted from this image; no operational
  EoIP claim follows.
- USB/IP settings UI and linked HTTP storage code image gate passed.
- Discovery and KMS status, SSH and iPerf3 status/handler, and ZeroTier
  dependency, localization, status, and group-control image gates passed.
- The complete firmware upload, ZIP, and download jobs completed successfully.

The BusyBox report produced by #488 predates the local audit-contract correction
now in the working tree: it previously used selector-classification coverage
as the value for `selected_service_entrypoint_map_complete`. The corrected
report separates selector classification from actual active-service entrypoint
coverage and now checks that each active selector is mapped to its service.
Local synthetic checks reject a missing map, omitted active selector, missing
image check, or failed image check. The corrected report remains pending a new CI run.
Therefore #488 is not cited as proof of the corrected field semantics.

## Limits and remaining work

- A successful build and ROMFS gate do not prove router-side settings save,
  process lifecycle, listener reachability, service connectivity, or reboot
  persistence. No router state was changed and no firmware was flashed.
- EoIP remains unavailable in this profile because its selector is disabled;
  test its UI and runtime only if it is deliberately selected in a future
  image.
- Continue the required exact-image BusyBox audit across enabled service
  lifecycle/error paths. The selector-driven gate is not a substitute for that
  audit.
- Preserve device runtime acceptance as a separate supervised step.
