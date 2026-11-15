# Pairing target candidates before ROMFS assembly

Optional peer82 already builds an isolated MT7603 module and complete RC/HTTPD
binaries. The normal TRX is built before those candidates and does not thereby
include them. `paired-image-inputs.json` now records exact source revision,
input report hashes and payload hashes for subsequent isolated image assembly.
It checks ELF32 LE MIPS and ELF type, matching module report, RC/HTTP dependency
report identities, paired IAPP policy and CONFIG_PM disabled. It refuses missing,
empty, symlinked or mismatched inputs. This is not an installation tool.

Pinned SDK Makefiles install RC at `/sbin/rc`, HTTPD at `/usr/sbin/httpd` and IAPP
at `/usr/bin/iappd.sh`. The RC dependency closure probe uses a temporary
`candidate:usr/sbin/rc` staging identity; that identity is not its firmware path.
The package records the actual SDK RC path. Existing `/init` and `/sbin/init`
symlinks and other RC multicall links must remain intact during final assembly.
The module is identified as `driver:mt76x3_ap`; its actual image destination
must be discovered from the assembled baseline module tree and verified before
replacement. No guessed kernel module path is admitted by this manifest.

The manifest keeps production_installed, TRX inclusion and physical runtime
false. Final assembly must verify source/run identity, stage these exact payloads
into an isolated baseline ROMFS, preserve configuration and paired IAPP policy,
verify dependency closure at actual destinations, rebuild the image and inspect
its extracted contents. An old successful candidate cannot establish inclusion
of newer boot/root code. Physical WR1200JS acceptance remains separate.

## Isolated ROMFS staging tool

`stage-candidate-romfs.py` consumes the exact pair manifest and regenerates its
input checks before copying anything. Output must be new and disjoint from the
baseline/results. Baseline and candidate kernel config bytes must match; a
configured driver built against a different kernel cannot be combined silently.
A coherent configured-kernel candidate build is required on mismatch.

The tool discovers one regular `mt76x3_ap.ko` below actual `lib/modules`, rejects
aliased replacement files/parent symlinks, and replaces that module, `/sbin/rc`,
HTTPD and IAPP only in the new copy. All unrelated entries, modes and symlink
targets must compare exactly, including RC multicall links and saved defaults.
The original baseline is rehashed and must remain unchanged. Failed post-copy
verification leaves an unaccepted output for diagnosis; it never edits baseline.
The report explicitly does not claim actual-path dependency closure or TRX build.

`check-stage-candidate-romfs.py` covers synthetic positive staging and config,
source, duplicate module and symlink refusals. Real candidate/baseline staging,
actual-path closure, image build/extraction and device verification remain open.

## Real optional staging is now wired

After peer82 target link and pair-manifest generation, the optional workflow
calls `ci-stage-candidate-romfs.sh` on its real baseline ROMFS and kernel config.
Kernel-config mismatch records `isolated-romfs-kernel-config.diff` and fails;
it is not treated as permission to combine the module with another kernel.
The isolated staged tree is checked for actual-path RC/HTTPD dependency closure
and module vermagic 4.4.198. Hashes in the dependency report must match staged
payload hashes. Only then does the staging report mark actual-path closure true.
Reports remain in the existing candidate artifact; the temporary copied ROMFS
is deleted by its owning script. No TRX build or normal-image replacement is
performed by this step. CI execution of this new step remains pending.
