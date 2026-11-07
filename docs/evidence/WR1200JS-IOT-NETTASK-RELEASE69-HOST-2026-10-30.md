# Network tasklet release fence69 — host verification, 2026-10-30

Isolated candidate: `.iot-local-check/nettask-release69c-20261030`, prepared
by `tools/iot/prepare-nettask-release-fence.py` from pinned schedule68b.
The adapter release gate now requires joined tasklets, blocked/drained
submission ownership and no initialization in progress. It permanently fences
reopen before checking peer state. A failed later peer check leaves that fence
in place. Initialization reserves its lane under the same tasklet lock before
allocating task storage; exit refuses an active initialization reservation.

Actual extracted helper/Init/Exit host assertions passed with strict GCC
C11/O2/Wall/Wextra/Werror, both base and extended feature definitions
ANDES_SUPPORT, MT_MAC, CONFIG_ATE, UAPSD_SUPPORT, CONFIG_AP_SUPPORT, DFS_SUPPORT.
New assertions cover duplicate initialization reservation and exit refusal
without task storage mutation. Freshly compiled adapter-release fixtures
passed with and without WSC_INCLUDED. Outputs use nettask-release69d names
under .iot-local-check; generated files are not publication artifacts.

Locks, scheduling, allocation and waits are mocked. These sequential tests
are not kernel concurrency, MIPS ABI, module linking, image or device proof.
OS_ABL task allocation failure handling remains unverified. Candidates67–69
remain isolated; the composed preparer chain still ends64, with draft65
excluded. Full fixture adaptation/composition and target compilation remain
required. Terminal PCI release receipt and child callback retirement bindings
remain open; this gate does not manufacture those prerequisites.

No router changes, firmware build, workflow dispatch or publication in this
verification step. Published standalone tasklet model is fec63dd; other local
work is preserved. Sol remains the single writer.
