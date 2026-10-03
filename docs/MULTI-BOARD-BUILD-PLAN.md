# One workflow run, several board images

Human request, 2026-10-03. Implementation is pending; CI currently builds only
WR1200JS. Second device already runs Padavan 3.4 and has no Breed; user has no
physical access. Exact device remains unidentified.

## Required structure

- Keep configs.build/wr1200js.config as the full existing WR1200JS profile.
- Add a separate reduced profile only after identifying the second board.
- Use a GitHub Actions matrix with explicit board, config, source revision,
  board-port entry point and image-verifier fields. Do not scan arbitrary
  config filenames and assume every file is a supported build target.
- Each matrix job receives its own runner/source tree/ROMFS and board-specific
  artifact name, requested/effective firmware and kernel configs, checksums,
  product identity, CRC and partition-size verification.
- Set fail-fast: false so failure of one board does not cancel another.
- Separate shared package integration from WR1200JS-specific DTS, partition,
  radio, USB merge, product checks and isolated MT7621 systick link experiment.
  The present workflow hardcodes all of these and cannot safely be generalized
  by replacing only its make target.
- Retain WR1200JS features. Document each reduction in the second profile and
  retain required remote-access packages if the user relies on them there.
- Admit the second target into the normal matrix after its Linux 4.4 board
  port and image checks compile successfully. A Linux 3.4 image, if requested
  as a separate fallback, must be clearly labelled and not called a 4.4 port.

## Next evidence

Use collect-second-router-identity.sh through an existing SSH session if
available. It reports kernel, firmware identity, SoC, RAM, MTD partitions and
loaded modules without changing settings. Firmware productid can be inherited
from a generic image, so cross-check it against SoC/radios and flash layout.
Do not request credentials or dump all nvram values.

Inspect the pinned nilabsent XIAOMI and XIAOMI-U-Boot board definitions as
references after identification. Their existence under Linux 3.4 does not
establish Linux 4.4 support or compatibility with the installed bootloader.
Keep flashing outside this CI change. No remote update/reboot is authorized.
