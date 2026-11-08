# WR1200JS toolchain transition review — 2026-11-08

A/B run [42478470441](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/42478470441)
built both firmware images successfully at source
65084db1496f03bc2f06e8e6876583456aa35ce2. The historical comparison job failed
on exact implementation filenames, not on compilation or a reported ABI change.

| Item | Control | Candidate | Difference |
| --- | ---: | ---: | ---: |
| Firmware image, bytes | 13,064,585 | 13,071,901 | +7,316 (0.056%) |
| ELF files | 287 | 287 | 3 versioned names replaced |
| ld-uClibc, bytes | 68,676 | 68,744 | +68 |
| libthread_db, bytes | 22,796 | 22,828 | +32 |
| libuClibc, bytes | 652,676 | 718,452 | +65,776 |

GCC remains 10.5.0; uClibc changes 1.0.43 to 1.0.48. Of 284 common ELF paths,
250 are byte-identical and 34 have changed hashes. Their recorded ELF class,
endianness, machine, architecture/ABI flags, NEEDED entries and interpreters
are unchanged. Firmware/kernel config hashes are equal. Size is not a runtime
RAM or performance measurement.

## Exact-image review

The [transition evidence](evidence/WR1200JS-LIBC-TRANSITION-65084DB-2026-11-08.json)
was generated from downloaded firmware artifacts, with image SHA256 and every
ELF digest matched against the original reports. Both SquashFS roots were
extracted locally; no device operation was performed.

All 29 needed library names and all declared interpreter paths resolve within
each image. In particular libc.so.0 and ld-uClibc.so.0/.1 resolve to the matching
candidate implementations. The three libraries keep identical recorded ABI
metadata and SONAMEs; their public SONAME aliases resolve to the reviewed files.
No previous exported dynamic symbol name disappeared: the loader adds one,
libc adds six, thread_db adds none. This is static software evidence, not proof
of identical behavior, function signatures or runtime stability.

Nine inherited ELF RPATH entries still mention the build stage directory in
both images. They did not change, and required libraries resolve through the
shipped lib/usr/lib paths. This inherited packaging issue is recorded separately;
it is not silently described as a new toolchain regression or complete RPATH audit.

## Implemented comparison correction

[review-libc-transition.py](../tools/toolchain/review-libc-transition.py) verifies
the exact images, ELF hashes, renamed-library ABI/SONAME/export names and image
loader/dependency paths. The comparator accepts only the three explicit
1.0.43-to-1.0.48 implementation renames when this matching evidence passes.
Unknown files, ABI changes, removed exports, missing libraries, unmatched image
hashes and changed configs remain failures. CI now runs this review before
comparison; it does not skip the comparator or disable its safeguards.

[Replayed comparison](evidence/WR1200JS-TOOLCHAIN-REVIEWED-COMPARISON-65084DB-2026-11-08.json)
passes locally for the existing images. This does not change the historical
GitHub run's conclusion. A fresh exact-SHA CI result must be recorded separately.
Negative gates and an actual broken-libc-alias check passed.

## Applying the new compiler

1. Complete the corrected software CI review while retaining the control.
2. Preserve the exact source-built candidate and its sources/report/licenses
   in a distinct owned Release; a seven-day Actions artifact is not permanent
   compiler storage. Pin its digest and reviewed generator provenance.
3. Change the development compiler selection to that owned, verified candidate
   in one focused package; retain an explicit control/rollback selection.
4. Build the first ordinary WR1200JS image at the selection-change SHA and
   continue IoT, then the new WebUI. Physical acceptance is deferred by the
   owner until those are ready; it is not a prerequisite to this development
   compiler selection. Do not label the device runtime verified.

The current default remains the control until that selection package is made.
Automatic compiler generation remains disabled; only manual workflow dispatch
can rebuild the toolchain. This review never flashes or restarts the router.
