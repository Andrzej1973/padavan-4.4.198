# Preserved local Nim helpers

Reviewed on 2026-11-21 during the local merge preservation audit. These
standalone tools are development inputs, not native-driver or router evidence.
Their existing source behavior was preserved; generated binaries stay local.

| Source | Purpose | Observed behavior |
| --- | --- | --- |
| [IE length model](../ie_length_check.nim) | Model lengths, offsets and remaining capacity | Default six-case demonstration deliberately reports one FAIL and exits1 for an unchecked oversized input |
| [Slot lookup model](../slot_lookup_check.nim) | Compare MAC-only lookup with interface/generation predicates | First example prints PASS=false, two strict examples print PASS=true; exit0 is not an aggregate test verdict |
| [Text replacement helper](../tools/replace_text.nim) | Explicit byte-string replacement in a specified file | Temporary-file demonstration replaced the first of two matches and exited0 |

All three were compiled/run with `nim c -r` using temporary output/cache paths.
The IE CLI accepted an exact remaining-capacity payload (20-byte buffer,
offset10, header2, payload8) and refused payload9; both explicit expectations
exited0. These checks exercise the Nim models only. They do not verify actual
C input parsing, station lookup, DMA ownership or firmware runtime behavior.

The replacement helper defaults to the first occurrence; `--count:N` requests
an exact positive count and `--all` replaces all matches. It writes a temporary
file beside its target, preserves permission bits and checks the original
content before replacement. It is intended for the project's single writer;
this check is not an interprocess lock or a concurrent-edit transaction.
Only the first-occurrence demonstration was repeated by this review, not a
complete utility test matrix. Use it only with an explicit intended target.

Temporary compiler outputs/cache and sample text were removed by
TemporaryDirectory. The pre-existing generated binaries were preserved rather
than deleted as part of this audit. Do not stage those binaries or infer firmware
acceptance from these helper results.
