# WR1200JS build 425 evidence

Checked 2026-10-18. Source commit: `ea0bac29ec2f167097d3285ceeaa7526f8e0c697`.

- Firmware run [39093587412](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39093587412): completed, success.
- Service checks [39093587422](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39093587422): completed, success. The Linux file-only archive fixture checks private-directory repair, unchanged record contents/mode, repeat invocation and rejection of symlinks/non-directories.
- Downloaded distribution contains firmware, `wr1200js.config` and `SETUP_WR1200JS.txt`.
- Firmware: `WR1200JS_4.4.198.9-425_ea0bac29.trx`, 12,615,687 bytes; SHA256 `db61e68d620c84b6fb6f521b9bb7c593f3fd037aaa3aadabc8b400227dc11653`.

7-Zip independently extracted `sbin/mtd_storage.sh` from the downloaded TRX.
Running `tools/vpn-profiles/prepare-storage-permissions.py` with
`--verify-image` against that extraction passed: the private-directory helper
and both load/restore call sites are present in the shipped filesystem.

This establishes CI fixture and final-image inclusion evidence. It does not
establish physical storage persistence, successful boot or independent concurrent
WG/AWG tunnel operation. No router connection, flash, reboot or service restart
was performed; the management tunnel remains disconnected by the user.
