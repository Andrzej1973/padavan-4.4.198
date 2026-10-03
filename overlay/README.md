# Experimental Hadzhioglu package overlay

This overlay is applied by pre-build.sh into the cloned padavan-ng source tree before clear_tree.sh.

Current packages:

- vlmcsd: KMS server, based on Hadzhioglu package trunk/user/vlmcsd
- ndisc6: ndisc6 + rdisc6
- socat: lightweight socket relay utility

The original Hadzhioglu package Makefiles expect pre-downloaded source archives in the repository. The experimental overlay makes the three packages self-contained by downloading and extracting their pinned source versions during the build.

Build hooks added to trunk/user/Makefile by pre-build.sh:

- CONFIG_FIRMWARE_INCLUDE_VLMCSD -> vlmcsd
- CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6 -> ndisc6
- CONFIG_FIRMWARE_INCLUDE_SOCAT -> socat

obfs4 is deliberately NOT enabled in this first experiment because the current Hadzhioglu package pulls an Entware obfs4proxy package and the user's estimated package size (~6 MB) can materially affect the WR1200JS 16 MB flash budget.

No binary blobs are committed to this repository by the overlay; the package Makefiles download their upstream sources during the firmware build.