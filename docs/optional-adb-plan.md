# Optional ADB build plan

Keep `# CONFIG_FIRMWARE_INCLUDE_ADB=y` commented in configs.build/wr1200js.config.
Uncommenting must eventually select a verified Android Debug Bridge host tool,
not ADBYBY (a different package). This feature is not yet ported.

Source evidence (2026-10-03):
- Pinned 4.4 base vipshmily/padavan-4.4 c25283e915a2a00a763774dd255b14aff997285e
  has no ADB entry in trunk/user/Makefile and no trunk/user/adb directory.
- Baseline nilabsent/padavan-ng d2c5846299949c57a4e867284069900b561dd2a4
  has trunk/user/adb sources and a host-tool recipe.
- Recipe links libcrypto, pthread and zlib, uses usb_linux.c, and installs /bin/adb.

Required work:
1. Preserve pinned source origin/licenses and port the recipe and selector.
2. Verify OpenSSL 3.5 API compatibility, pthread/zlib linkage, USB device access
   and the selected MIPS/uClibc compiler.
3. Keep the default selector disabled; verify both disabled and enabled builds.
4. Inspect /bin/adb, target ELF dependencies and image capacity in the enabled build.
5. Verify connection with an authorized Android device after base router runtime
   and recovery access are established. Do not auto-enable a network listener.
6. Document the actual ADB version and limitations from the source/build result.

Commenting the selector does not implement the optional build path. No successful
ADB build or router/device connection is claimed here.
