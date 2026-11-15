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
