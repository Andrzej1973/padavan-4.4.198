# WR1200JS test build 322 — WAN effective port and ZeroTier refresh

Full run [38842496655](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38842496655)
succeeded at `4b74897cd483e4672fe40c204b9d6c2459e86651`.
Package artifact 12022451109, WR1200JS_4.4.198.9-322_4b74897c_TEST,
was downloaded into ../build322-final. Exactly three files:

- TRX: 12,623,063 bytes, SHA256
  `85864aeb20042a039ca5d598b7cf96dddecaab7c404fb3d6e4006a2f3ab7f260`.
- SETUP_WR1200JS.txt: 39,470 bytes, SHA256
  `f0b931eea30e942a60b1fe0754af580e50449ad8021acb12f4c0dd6ce1a5c69a`.
- wr1200js.config: 11,333 bytes, SHA256
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

Independent local upload-structure verification passed all six checks.
The profile is byte-identical to configs.build/wr1200js.config. The packaged
guide passed the updated checker including ZeroTier status usage guidance.
Downloaded WAN report artifact 12022291245 is preserved as
WAN-BUILD322-IMAGE.json: all 26 checks true, runtime_verified=false.
It includes the effective-port panel markers and EN/UK/RU labels.

Local archive ../WR1200JS_4.4.198.9-322_4b74897c_TEST.zip contains exactly the
three package files and passes ZIP CRC validation. Size 12,586,306 bytes;
SHA256 `3cb1c64721738426839d4830c16b7f7e2b66db016b26a02939912816f4380230`.
This checksum identifies the locally assembled ZIP, not GitHub's ZIP container.

This image includes effective-WAN link monitoring and socket mismatch display,
ZeroTier freshness semantics, bounded JSON cache text refresh/nonblocking open,
and corresponding setup guidance. The later a626c05 change only updates the
PC-run diagnostic collector/docs; it does not change the firmware image.

No flash/reboot/port reassignment was performed. Compilation, artifact structure
and static image checks do not prove router boot, traffic, isolation, persistence,
DNS, VPN connectivity or sustained stability. Physical acceptance remains open.
