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

To preserve the already reviewed source run42467546674 without compiling again,
set preserve_existing=true and publish_candidate=true in the manual dispatch.
This skips the build job, verifies the original run/revision, all archive hashes,
license and source inventory, and creates a separate owned prerelease on the existing reviewed tag
`toolchain-source-candidate-v1` (exact generator SHA checked). The maintainer
creates that tag through normal Git before dispatch; Actions cannot create an
unreviewed historical workflow ref. Publication uses --verify-tag and does
not select the compiler as default. No push/PR event is enabled.

Output includes the compiler archive, source/recipe/config archives, original
Linux/libc inputs, downloaded package archives, installed licenses, logs,
SHA256SUMS and result.json. The builder relocates the compiler before compiling
MIPS32r2/O32 C and C++ probes. It checks libc/header versions and runs pthread,
TLS, math and C++ exception probes under qemu-mipsel. QEMU user-mode success
is not WR1200JS device acceptance. Host-GCC fixtures are not target builds.

The optional publish_candidate input creates a distinct prerelease with these
archives and hashes after success. It never overwrites build-toolchains-v1,
changes sources.lock.json or promotes the compiler to production automatically.
WR1200JS development firmware now defaults to the preserved source compiler
after software A/B42482182188 passed. The original byte-preserved compiler
remains selectable as pinned for explicit control/rollback builds.
Physical acceptance is deferred by the owner until IoT and the new WebUI are
ready; it does not block the development compiler selection.

This recipe pins its principal inputs and records resolved configuration/source
hashes; it does not yet claim bit-for-bit reproducibility across host images.
Runner packages, timestamps inside compiled objects and package build behavior
can still affect bytes. License installation and source archives are preserved;
a complete per-component distribution/license review is a separate gate.

Monitor watched paths/names are extended for this workflow, with offline
failure-once/success-silent regression. The deployed monitor still checks out
trusted main, so those changes take effect there only after normal integration.
Do not weaken that trusted-checkout rule to monitor an experimental branch.

Reviewed source candidate preservation succeeded in run42483890602.
[Owned candidate Release](https://github.com/Andrzej1973/padavan-4.4.198/releases/tag/toolchain-source-candidate-v1)
contains all three source/binary archives and metadata. GitHub asset digests
were compared with the original archive hashes. Do not redispatch preservation
for this already complete Release; it does not overwrite existing assets.
The subsequent development-selection package changes the WR1200JS default
to source; explicit pinned control remains available in Run workflow.

Source-variant firmware downloads now use configs/owned-source-toolchain.json
with immutable owned asset IDs and SHA256 for the compiler and result.json.
Both files are cached by digest and revalidated, including generator/ABI
provenance; no expiring Actions-artifact fetch or foreign fallback is used.
The pinned control download path is retained. Compiler verification tools
come from the dispatch SHA in a separate CI-only sparse checkout; firmware
source may be an older exact ancestor. The artifact records both firmware and
loader revisions. This prevents an older source from missing the newer loader.
