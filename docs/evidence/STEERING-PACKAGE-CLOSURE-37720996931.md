# Driver-matched steering package and rc closure

Inspected downloaded artifacts on 2026-10-08.
Full workflow 37720996931 and ABI workflow 37720996405 completed successfully
at aa0a2f2a8198afb7c5e009940d1cf72aac290aa2.

Artifact 11526293529 (band-steering-driver-package-probe):

- wr-band-steering: 59104 bytes; SHA256
  c418cc0d9105ca853711bad9ba8ee3571279edcc75485b3edf413b1ca815e841.
- wr-band-steering-ctl: 10660 bytes; SHA256
  c05693c92822f889f87852b506d294e238ca0903b69de609a1f337564bb25c21.
- Protocol layout generated from the actual prepared driver ABI: SHA256
  34a02d5cc61264966155a140ce8a8cdd652a33baf5b899b40361402837155096.
- dependency-closure.json: verified, no errors; four ELF files including
  image dependencies and loader.

Artifact 11526258582 (band-steering-full-rc-profile-probe):

- rc-dependency-closure.json: verified, no errors; six ELF files.
- Actual net_wifi.o symbol report contains wr_radio_snapshot (local BSS),
  wr_band_snapshot_capture, wr_band_profile_bind_snapshot and release/unbind.
  This supports target compilation of the latest radio snapshot integration.

The checker proves recursive DT_NEEDED files, ELF32 little-endian MIPS headers
and image-root interpreter resolution for these artifacts. It does not validate
every imported symbol, library ABI, successful execution, driver event exchange
or Wi-Fi behavior. Binary bytes are uncompressed ELF sizes, not TRX growth.
Both reports explicitly retain production_installed=false and runtime_verified=false.
The normal firmware still does not install this steering candidate.

Next: conditional normal-source integration, factory-disabled WebUI controls,
and complete image checks, followed by recoverable device acceptance.

