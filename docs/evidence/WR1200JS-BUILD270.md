# WR1200JS test build 270 — MT76x2 file-handle guard

[Run 38610879180](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38610879180)
completed successfully at commit `3cb3fcf565996786aca21c5642deb866941c2914`.
Artifact `WR1200JS_4.4.198.9-270_3cb3fcf5_TEST`, ID `11917747350`, was
downloaded into the parent workspace's `build270-final` directory.

Independently computed SHA256:

- `WR1200JS_4.4.198.9-270_3cb3fcf5.trx`: 12,589,514 bytes;
  `2bbefa89158caacfab4aa8d4959ac8896506b4e7b69a4a3f7edd50976ecf6d42`.
- `SETUP_WR1200JS.txt`: 23,353 bytes;
  `4237aed1f4b9d28f2a70edcea9cedec19d84a83e7a9233d1712387f4a93139cb`.
- `wr1200js.config`: 11,333 bytes;
  `f8021c77617feebb930fcdeb51bf7f9547d47628abfe5ae2dbd2475572308baf`.

Downloaded config is byte-identical to the requested profile. Guide identity
contains `270_3cb3fcf5`. StrongSwan remains deferred; CAKE remains excluded.

The full-build log confirms guard preparation at 17:57:19 UTC, compilation of
`mt76x2/os/linux/rt_linux.o` at 17:58:21 UTC, and linking `mt76x2_ap.ko` at
17:58:40 UTC. This establishes source preparation and compilation in the
actual radio module, beyond the isolated test fixture.

[Native service run 38610878782](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38610878782)
passed the generated guard test with address/undefined-behavior sanitizers:
NULL, ERR_PTR, valid and unreadable file handles. The fixture substitutes a
minimal file structure and read primitive; it does not execute the Linux VFS.

This image has not been installed by this work. Guard behavior under real
driver file-open failures, calibrated radio operation, Wi-Fi/HWNAT stability,
configuration retention and reboot persistence remain unverified. No claim
that this guard fixes the reported Wi-Fi freeze is made.
