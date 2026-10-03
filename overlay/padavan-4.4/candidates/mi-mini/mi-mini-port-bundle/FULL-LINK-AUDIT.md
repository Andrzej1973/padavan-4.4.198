# Mi Mini full-kernel link audit

Observed failure: new repository run 37133812766, job 111234099057,
source revision ad5ab44cfc4e021027c9cfbbd1679324e86d929f.
The compile proceeded to LD vmlinux.o and final link; unresolved symbols:

- `__gpiod_export`: vendor gpiolib-of export calls need GPIO_SYSFS.
  The probe now explicitly enables/checks GPIO_SYSFS after olddefconfig.
- `procRegDir`: legacy radio expects an RDM-owned global which is absent in
  the pinned 4.4 link. The isolated Mi Mini candidate now owns a private
  pointer for its existing /proc/mt7620 directory. Other legacy builds retain
  their external declaration. The VIDEO_TURBINE feature remains disabled.
- `ra_mtd_write_nm`: still unresolved; requires checked Factory write binding.

These first two repairs are source candidates, not a successful kernel link.
Clean reconstruction matches all 273 candidate files. Do not enable the board
for firmware-image builds until the remaining full port and image checks pass.

## Factory write requirements before next full-link probe

The pinned bridge exports mt_mtd_write_nm_wifi, but its implementation only
checks len <= erasesize, uses memcpy(bak + to, buf, len) without checking
to + len, only warns about a short backup read, always erases offset zero,
and does not check the final write's returned length. Directly aliasing the
legacy name would not establish a checked EEPROM writer.

Implement a separate Mi Mini-scoped adapter with Factory-relative bounds,
complete erase-block backup, preserved unrelated calibration bytes, serialized
read/modify/erase/write, completed erase handling, checked read/write lengths,
balanced MTD references and real error propagation. Keep automatic reset of
invalid Factory calibration blocked in initialization. Review all legacy
write callers and their failure contracts; do not use success-returning stubs
or bypass the write path merely to obtain a successful link.

Actual partition layout and calibration must still be verified on the device.
No router Factory write, flash or reboot has been performed or authorized.
