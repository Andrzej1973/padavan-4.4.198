# MT7620 radio port candidate bundle

radio-source.diff contains four changed C files and the replaced candidate
Kbuild Makefile. new-files contains two Kconfig files, the Factory helper and
platform glue. manifest.json pins
the upstream commit/tree and records new-file and patch SHA256 hashes.
Upstream bytes remain preserved separately under mi-mini-driver-full.

Apply the diff to a fresh verified driver tree, then copy new-files. Stage that
tree at drivers/net/wireless/mediatek/mi-mini in a separate pinned4.4kernel,
source its Kconfig and add its directory to the parent Kbuild. Integrate the
checked Factory helper in built-in wifi_utility using integrate-mi-mini-factory.py.
Configure SOC_MT7620/MI_MINI_RADIO and verified radio feature options. The radio
DTS fragment is disabled and no complete board DTS or bootable image is provided.

Compilation/linking/runtime remain unverified. This is not a release artifact.
Keep upstream license notices and module license declarations unchanged.
