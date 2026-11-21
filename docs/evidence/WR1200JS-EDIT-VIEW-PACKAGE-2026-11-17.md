# IoT edit/view source package

Base: `87f2ed5ab8555bedc177d37b4e6d2d9a211a96f2`.

Implements a nonsecret desired-configuration view, private expiring RC revision
ownership, explicit KEEP/REPLACE edits, typed single-mailbox transport, guarded
handoff to the existing RAM/Save owners, separate RC view endpoint and guarded
HTTP view/edit routes. Prepared WR startup installs Save/edit/view in order;
unavailable native capabilities refuse installation without blocking boot.
No new native persistence writer or firmware ACK/TX/DMA modification is included.

The Classic form and its exact-baseline preparer are candidate assets. They
distinguish requested state, queue acceptance, RAM and confirmed flash results;
unknown outcomes do not automatically replay POST. Form preparation is not
main-image promotion. Draft labels are Ukrainian; full localization, rendered
browser verification and final-image integration remain required.

Verified host evidence:

- `check-config-edit-suite.py --native-linux
  .scratch/config-transport-20261117/native-linux-fresh.c --native-http
  .scratch/http-view-native`: session24755 completed exit0, log
  `.scratch/config-edit-suite-final.log`. Includes actual store/parser/guard,
  queue/RC/RAM/Save/fork worker composition, real Unix socket tests, strict
  HTTP/JSON checks, isolated source staging and simulated Classic DOM.
- `check-physical-stop-client-preparation.py`: session35986 completed exit0,
  log `.scratch/edit-package-source-final2.log`; generated startup and exact
  source-equality checks, deliberate corruption/duplicate refusal. Its AST
  selector now locates the inner unit loop by type/name.
- RC edit-result observer focused regression completed exit0 in
  `.scratch/edit-runtime-observer.log`.
- Target-link shell syntax passed. New required RC/HTTP symbols are checked
  by the target-link script; those checks have not yet run for this package.

Boundaries: native NVRAM/flash/SDK and some capture/clock/entropy operations are
actors in host composition. No source/host result establishes MIPS build,
TRX/ROMFS correctness, physical RF/DMA completion or router acceptance. The
source metadata leaves target/runtime/production readiness false. Published
optional1373 concerns the base hotfix revision, not these local additions.

Remaining: build this exact package on GitHub; inspect target symbol/dependency
and image evidence; compose the rendered Classic page with HTTP and actual RC
service end to end; complete localization and image inclusion; continue IoT
activation/main-image gates. Device changes require separate owner permission.
