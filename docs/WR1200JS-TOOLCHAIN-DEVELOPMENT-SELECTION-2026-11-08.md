# WR1200JS development compiler selection — 2026-11-08

Software gate passed: [A/B42482182188](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/42482182188)
at source1aff9470c8fac1b51244434a2016d6b5db5cedfe. Both full image jobs and
the exact-image libc/ELF comparison succeeded. The downloaded comparison
artifact was independently checked; [evidence](evidence/WR1200JS-TOOLCHAIN-AB-1AFF947-2026-11-08.json)
retains configs, image hashes, ABI/SONAME/export-name and dependency/loader checks.
This is software evidence, not device acceptance or full behavioral ABI proof.

WR1200JS firmware now requests `source` by default: preserved MIPSel GCC10.5,
uClibc1.0.48, Linux4.4.198 headers from generator
5ef6a8577ae24be27d8d81b3fe44a587d8491a16. The compiler archive remains exactly
5a9254920f52954b2910ad968086135436e320bfb1360928cf96f4f0bf03870a.
[Owned Release](https://github.com/Andrzej1973/padavan-4.4.198/releases/tag/toolchain-source-candidate-v1)
retains compiler, sources, licenses and reports; binary and metadata downloads
use committed asset IDs/hashes and a validated cache.

In **Build selected router firmware → Run workflow**, choose `pinned` to build
an explicit original GCC10.5/uClibc1.0.43 control. A/B always sets pinned/-control
and source/-source explicitly, so changing the ordinary default cannot silently
turn both comparison lanes into the new compiler. The original archive is not
overwritten. Other board/diagnostic compiler selections are unchanged.

Compiler verification scripts/config come from the workflow dispatch revision
in `.toolchain-verification`, a sparse checkout confined to the CI runner.
Firmware source remains the requested exact revision in the main job checkout.
This supports older optional source revisions without looking for new compiler
loader files in their historical tree. `toolchain-loader-revision.txt` records
that separate tool revision beside the compiler hash and firmware source ID.
No new clone/worktree is created in the shared WSL workspace.

The focused selection package needs its own ordinary firmware CI result at
its new SHA; the earlier A/B does not cover this workflow wiring. Required
isolated IoT target checks keep their exact source/compiler scope. Device boot,
Main/Guest/IoT RF behavior, hardware drain and runtime stability remain open.
The owner deferred physical acceptance until IoT and the new WebUI are ready;
it is not a gate on this development selection. Router settings, ACK safety,
flash layout and hardware feature defaults are not changed by this package.
