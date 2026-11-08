# Source-built WR1200JS toolchain candidate

The pinned mechanism in nilabsent/padavan-ng (c29b12da69b1593a6e8cf65cd43767fc99bb6386)
is crosstool-NG bootstrap/configure, sample selection and source compilation.
Its profile uses GCC7/Linux3.4 and custom libc. This project uses the same source
build architecture with the existing Padavan4.4 GCC10 profile; it does not copy
nilabsent's kernel/libc ABI into WR1200JS.

Inputs are in toolchains/wr1200js/sources.json and crosstool.config:

- crosstool-NG1.26.0 official archive, SHA256 pinned after checking its official
  SHA512 file. Its GCC10 default selects10.5.0 and binutils2.40.
- Padavan source c25283e915a2a00a763774dd255b14aff997285e supplies actual
  Linux4.4.198 headers and the board's uClibc config, via sparse Git checkout.
- uClibc-ng1.0.48 is a custom source archive with pinned SHA256. ct-ng1.26.0
  bundles release metadata only through1.0.43, so silently accepting a different
  library would be incorrect. The archive comes from Buildroot's source mirror;
  its upstream release URL is preserved in the lock. This checksum was recorded
  from that TLS mirror download, not claimed as an upstream signature check.
- ct-ng package downloads must pass their bundled SHA256 checks. Downloaded
  tarballs are cached and preserved in the source artifacts. This does not mean
  all dependencies are already mirrored in our own GitHub.

Run **Build owned MIPS toolchain** manually through GitHub Actions → Run workflow.
Only workflow_dispatch is enabled: pushes and pull requests do not rebuild the
compiler, including changes to its recipe or tools. Heavy compilation is refused
outside GITHUB_ACTIONS; the local checks only normalize/test the recipe.
The job has a separate queued concurrency group and a240-minute limit. It does
not block or replace the standard/optional firmware lanes.

Output includes the compiler archive, source/recipe/config archives, original
Linux/libc inputs, downloaded package archives, installed licenses, logs,
SHA256SUMS and result.json. The builder relocates the compiler before compiling
MIPS32r2/O32 C and C++ probes. It checks libc/header versions and runs pthread,
TLS, math and C++ exception probes under qemu-mipsel. QEMU user-mode success
is not WR1200JS device acceptance. Host-GCC fixtures are not target builds.

The optional publish_candidate input creates a distinct prerelease with these
archives and hashes after success. It never overwrites build-toolchains-v1,
changes sources.lock.json or promotes the compiler to production automatically.
Normal firmware continues using the existing byte-preserved toolchain until a
separate exact-candidate kernel/module/full-image regression and device gate.

This recipe pins its principal inputs and records resolved configuration/source
hashes; it does not yet claim bit-for-bit reproducibility across host images.
Runner packages, timestamps inside compiled objects and package build behavior
can still affect bytes. License installation and source archives are preserved;
a complete per-component distribution/license review is a separate gate.

Monitor watched paths/names are extended for this workflow, with offline
failure-once/success-silent regression. The deployed monitor still checks out
trusted main, so those changes take effect there only after normal integration.
Do not weaken that trusted-checkout rule to monitor an experimental branch.
