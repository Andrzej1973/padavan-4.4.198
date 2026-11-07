# WR1200JS QEMU dnsmasq seed-path correction

Date: 2026-10-21
Scope: test-harness correction for parsing the combined Stubby/DoH-generated
configuration with the final MIPS dnsmasq binary. This is not a firmware or
router change.

## Failure and source evidence

Firmware runs #509–#511 passed the VPN preparation step and built the WR1200JS
firmware, but failed in the subsequent `Resolve names through the image Stubby
under QEMU` step. The final `dnsmasq --test` exited 5 with:
`failed to seed the random number generator: Success`.

The exact pinned Padavan commit is `c25283e915a2a00a763774dd255b14aff997285e`.
Its dnsmasq 2.90 `src/config.h` sets `RANDFILE` to `/dev/urandom`; `src/util.c`
reads 128 bytes into the seed state and another 48 bytes into the input state.
The final `Success` text means errno did not explain the failed seed operation.
That is consistent with a short read from the image-root's device placeholder
under QEMU; the CI log does not directly show the file's type or contents.

## Correction

`tools/check-encrypted-dnsmasq-combination.py` now makes a temporary sysroot
overlay for the parser invocation. Root entries resolve to the built ROMFS,
`/dev/urandom` contains 4096 bytes from the CI host CSPRNG, and the generated
configuration is available at guest `/tmp/combined-dnsmasq.conf`. The source
ROMFS is only read; no image path or router state is modified. The existing
native emitter cases continue to run before the target parser invocation.

## Verification and remaining evidence

- Python AST parsing passed.
- `git diff --check` passed for the checker and updated evidence.
- Firmware run [#512](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39624109819)
  executed the corrected final MIPS dnsmasq/QEMU check successfully. The full
  firmware compile also completed. The run later failed the separate Privoxy
  `save_failure_apply_order` image assertion, so its downloads job did not
  publish a verified firmware image. This confirms the QEMU seed correction,
  not the overall image or service audit.
- No full firmware build was run locally; no firmware was flashed and no
  router service or setting was changed.
- The remaining item 4 image blocker is the Privoxy assertion. Details are in
  `WR1200JS-PRIVOXY-SAVE-FEEDBACK-2026-10-21.md`.
