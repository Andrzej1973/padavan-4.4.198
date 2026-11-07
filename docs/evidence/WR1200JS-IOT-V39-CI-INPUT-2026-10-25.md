# IoT v39 reproducible CI input (2026-10-25)

The 55 MT7603 source-overlay files from the isolated v39 tree are now staged
as ordinary, reviewable source under `tools/iot/candidates/aux-remove-close-v39/`.
They are the local v39 source with CRLF normalized to LF for stable Git and
Linux checkout bytes; no other source-byte change was made. The accompanying
`manifest.json` pins the 55 file hashes, 36 original Git blobs and donor
revision `c25283e915a2a00a763774dd255b14aff997285e`. The manifest
generator cross-checked all 31 blobs from the earlier reviewed manifest
against the pinned donor copy.

The existing optional firmware workflow accepts `iot_candidate_variant=v39`
when `run_candidate_checks=true`. Its default remains `legacy`. In v39 mode
it copies the versioned overlay into the already isolated candidate path;
the normal firmware build uses its unchanged production driver. The shared
assembler accepts only the reviewed 46/32 legacy and 55/36 v39 source shapes.

Local checks:

- Python syntax for the manifest generator and assembler passed.
- The versioned overlay matched the 55 local v39 source files after LF
  normalization. Git's staged blobs matched all 56 working files (including
  the manifest) byte-for-byte, and each manifest hash matched its source.
- The versioned manifest assembled against the saved prepared MT7603 tree:
  55 overlays, five three-way merges, one reviewed adapter-init conflict.
- All assembled output hashes matched; no conflict marker remained.
- The overlap checker returned its expected conflict code 1 with exactly five
  prepared modified files and 19 new candidate files.
- Both edited workflow YAML files parsed, and the new selector/default wiring
  was asserted; `git diff --check` passed for the workflow/assembler changes.

The versioned files and workflow edits are still local working-tree changes.
No commit, push, dispatch or MIPS build occurred in this step. Because v39
still lacks bound recovery and a safe PCI `remove` owner, even a passing
target compile would remain source/build evidence, not permission to package
or flash it. The next CI action is a single optional v39 candidate run after
a coherent reviewed commit and queue check; preserve all unrelated dirty work.
