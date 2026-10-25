# IoT v39 candidate build #588: AP-client declaration mismatch (2026-10-25)

## Exact run and failure

- [Workflow #588](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40195811064), commit `6d674142a811b69dfeaf463b655d0c7e869fa837`, used `run_candidate_checks=true` and `iot_candidate_variant=v39`.
- The normal firmware build completed before the isolated candidate step. The workflow failed at `Compile isolated merged IoT MT7603 candidate`; the downstream `downloads` job failed because the selected build job failed.
- Downloaded `iot-merged-driver-probe/build.log` reports `ap/ap_cfg.c:15059:8: error: void value not ignored as it ought to be` for `if (ApCli_Remove(pAd) != NDIS_STATUS_SUCCESS)`.
- The candidate implementation changed `ApCli_Remove` to `INT`, but omitted its declaration in `include/ap_apcli.h`, which remained `VOID`. The target compiler therefore treated the call result as `void`. The failure is in candidate source, not the ordinary firmware image.

## Minimal source correction

- `prepare-aux-remove-result-candidate.py` now updates the header declaration when generating the candidate.
- The versioned v39 overlay includes corrected `include/ap_apcli.h` with `INT ApCli_Remove`; its manifest pins 56 source files and 37 original blobs instead of 55/36.
- The strict manifest generator and prepared-source assembler accept this reviewed shape. Existing legacy 46/32 and prior v39 55/36 shapes remain supported by the assembler.

## Local checks and boundary

Python syntax checks passed for the three edited preparers. The updated manifest verified the pinned donor blobs and all 56 overlay hashes. The isolated merge into the saved prepared MT7603 source passed with five reviewed overlaps and the existing one-conflict adapter-init resolution. Both merged declaration and implementation are `INT`; no `VOID ApCli_Remove` declaration remains in the merged source. `git diff --check` passed for the targeted files.

This correction has not yet been target-compiled. It changes only the isolated candidate and its preparers; the production driver, firmware image and router remain unchanged. Next: publish the focused correction, let automatic baseline checks finish, then run one optional v39 candidate compilation with queue discipline and inspect its exact result.
