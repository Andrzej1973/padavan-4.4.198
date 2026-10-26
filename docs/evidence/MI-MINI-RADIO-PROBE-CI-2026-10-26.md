# Mi Mini isolated radio candidate — CI evidence (recorded 2026-10-26)

The diagnostic workflow is `.github/workflows/mi-mini-radio-probe.yml`. It
reconstructs the candidate from pinned kernel/radio sources, compiles the
MT7620 radio object, and links an isolated MIPS `vmlinux`. It does not produce
a Mi Mini firmware image or boot a board.

| Run | Commit | Result | Evidence |
| --- | --- | --- | --- |
| [38130857982](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38130857982) | `7c4a4dff8e652a5686e8d811d0e2f850da7abc95` | `compile-radio` succeeded on 2026-10-11 | GitHub job steps succeeded; log reports radio/MTD objects compiled, `LD vmlinux`, and explicitly says no board boot or firmware-image validation. |
| [37136824063](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37136824063) | `d201fda6271b844aa6a4d58b9868b2315d17e422` | `compile-radio` succeeded on 2026-10-03 | GitHub job-step result; no firmware or device result. |

The workflow uses pinned kernel `c25283e915a2a00a763774dd255b14aff997285e`
and radio source `d2c5846299949c57a4e867284069900b561dd2a4`.
On 2026-10-26 the GitHub artifact API returned `total_count: 0` for both runs;
the original diagnostic bundles could not be preserved from GitHub. The
workflow source and the run logs remain the reproducible record at this point.

**Acceptance boundary:** This confirms a narrow compile/link candidate only.
Mi Mini board DTS, Ethernet, full image, 2.4/5 GHz operation, repeater recovery,
IoT, and device acceptance remain unverified. Keep Mi Mini implementation after
WR1200JS acceptance as required by `docs/PROJECT-DELIVERY-SCOPE.md`.
