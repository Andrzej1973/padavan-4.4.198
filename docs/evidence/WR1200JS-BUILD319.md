# WR1200JS test build 319 — refreshing ZeroTier cache details

Full run [38841465981](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38841465981)
succeeded at `adca670ef116f6fe56c1dfd0ba0e1a168b87b574`.
The pre-compilation generated-C/JS status step succeeded as documented in
ZEROTIER-1.16.2-WR1200JS.md; the complete image also compiled and passed its
configured image gates. No device execution is established by these checks.

Artifact 12021418921, WR1200JS_4.4.198.9-319_adca670e_TEST, was downloaded
into ../build319-final. Exactly three files:

- TRX: 12,622,419 bytes, SHA256
  `93c15efe065d215b5b29e56eb9f40d211e9ea30fe393a9d5a782e97b2a5ca630`.
- SETUP_WR1200JS.txt: 38,286 bytes, SHA256
  `0a4c08c65a29561284d13e1eb098e7ea9bf00508de02941e923bad514816944f`.
- wr1200js.config: 11,333 bytes, SHA256
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

Local verify-wr1200js-image.py passes all six upload-structure checks:
uImage magic, WR1200JS product ID, header CRC, declared length, payload CRC,
and size bound. Original result WR1200JS-BUILD319-STRUCTURE.json has SHA256
`513e2808492d135328d7fc09ac2d39894575e57f5f1d23c537b2492f32a24095`.
This checks structure, not bootability or actual device flash capacity.

The packaged profile is byte-identical to the repository profile. The guide
passes content checks and identifies the correct full commit/build.

This image contains ZeroTier cache freshness labels and simultaneous JSON
refresh of bounded node/network text. It predates 9a7d16d's nonblocking cache
open and cde23db's effective WAN name/mismatch panel. Those must be verified
in a later completed image; do not attribute them to this package.
No router flash, reboot, configuration change or connectivity acceptance was
performed during this verification.
