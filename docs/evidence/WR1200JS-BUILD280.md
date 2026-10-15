# WR1200JS test build 280 — USB/IP inventory

[Run 38742194875](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38742194875)
completed successfully at `51777f00860764056d1f86436b0bc0e00bd25461`.
Artifact `WR1200JS_4.4.198.9-280_51777f00_TEST`, ID `11977431723`, was
downloaded into `../build280-final` on 2026-10-15.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-280_51777f00.trx`: 12,595,351 bytes;
  `7a8ef86d992c88b2e4abe2d0b5546e7b0e8ad05198bb8556f96d8d4184473ddb`.
- `SETUP_WR1200JS.txt`: 27,114 bytes;
  `944f02f6432add21e4d8e6a56508f704ce60a3fe2da37c66c64f56d6801d0304`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

The config SHA256 matches the requested profile and build 279. The guide
identifies `280_51777f00` and documents the inventory. The successful workflow
includes the image gate for the inventory handler string in HTTPD and the
refresh function in the packaged USB page. This establishes compilation and
packaging, not real HTTP/sysfs behavior. The separate service fixture at the
same commit is documented in `../USBIP-HADZHIOGLU.md`.

This image predates guarded manual bind/unbind (`f2ad65c`) and does not prove
their packaging or operation. It has not been flashed or tested on the user's
router. Browser rendering, safe-session Apply, physical USB enumeration,
driver binding, client transfer, access restrictions and persistence remain
unverified. The full device-port objective remains incomplete.
