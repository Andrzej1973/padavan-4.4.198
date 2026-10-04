# Xiaomi Mi 4 (MI-4) profile

The central profile is `configs.build/mi-4.config`, alongside WR1200JS and Mi Mini. It copies the current WR1200JS package selectors, including disabled optional packages, and changes the product identity to MI-4. No existing WR1200JS or Mi Mini selector was changed.

## Board evidence

The preserved source is `reference/boards/plumbum-13-padavan-4.4-tplink/trunk/configs/boards/MI-4`: board.h, board.mk, kernel-4.4.x.config and l1profile.dat. Its board.mk declares MT7621, 128 MiB RAM and zero USB ports. The kernel selects MT7603E/mt76x3 and MT7612E/mt76x2, device tree `mi-4`, NAND and UBI, with calibration offsets 0 and 0x8000. GPIOs and Ethernet port count differ from WR1200JS.

The pinned firmware base already supplies `arch/mips/boot/dts/ralink/mi-4.dts`: NAND firmware partition at 0x600000, length 0x1400000. These are source defaults, not confirmation of the user's bootloader or actual installed partition layout. WR1200JS SPI layout and image must never be substituted.

## Scheduling

The user explicitly schedules MI-4 image integration at the end of the WR1200JS firmware work. Finish the primary WR1200JS firmware first. This is a prepared package profile, not an enabled or verified build target.

## Remaining delivery work

Implement an MI-4 recipe using its preserved board data and matching pinned NAND device tree, carry over the common package ports and verify requested/effective selectors. USB-related software requests are retained as requested; zero physical USB ports cannot be changed by firmware. Verify actual package dependencies and packaging before claiming that all requests build.

Then enable MI-4 in the multi-board catalog and produce WR1200JS plus MI-4 images in the same workflow. Keep Mi Mini secondary. Final download remains one archive with separate model-specific TRX/config pairs. Initial status is build-disabled because no MI-4 image has yet been built or validated. Runtime acceptance and installed bootloader/partition compatibility remain required.
