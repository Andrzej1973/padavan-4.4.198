#!/bin/bash
# Verify standard Padavan package targets without changing the normal source.
set -euo pipefail
trunk="$(realpath "$1")"
layout="$(realpath "$2")"
probe="$3"
compiler="$(realpath "$4")"
test ! -e "$probe"
test -x "$compiler"
mkdir -p "$probe/trunk/user" "$probe/results"
probe="$(realpath "$probe")"
cp "$trunk/user/Makefile" "$probe/trunk/user/Makefile"
python3 tools/band-steering/prepare-package-integration.py "$probe" --layout "$layout"
parent_make() {
  make -C "$probe/trunk/user" ROOTDIR="$trunk" \
    PROJECT_CONFIG="$trunk/.config" LINUX_CONFIG="$trunk/linux-4.4.x/.config" \
    ARCH_CONFIG="$trunk/config.arch" CC="$compiler" \
    CFLAGS="-O2 -mips32r2 -mabi=32 -msoft-float" \
    INSTALLDIR="$probe/romfs" "$@"
}
for enabled in y n; do
  parent_make CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING="$enabled" \
    --eval 'wr-selection:;@echo $(dir_y)' wr-selection \
    > "$probe/results/selection-$enabled.txt"
done
grep -qw wr-band-steering "$probe/results/selection-y.txt"
! grep -qw wr-band-steering "$probe/results/selection-n.txt"
parent_make CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y wr-band-steering_only \
  2>&1 | tee "$probe/results/build.log"
parent_make CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y wr-band-steering_romfs \
  2>&1 | tee "$probe/results/romfs.log"
cross="${compiler%gcc}"
python3 tools/band-steering/verify-package-closure.py "$probe/romfs" "$trunk/romfs" \
  --readelf "${cross}readelf" --output "$probe/results/dependency-closure.json"
for binary in wr-band-steering wr-band-steering-ctl; do
  test -x "$probe/romfs/usr/sbin/$binary"
  cp "$probe/romfs/usr/sbin/$binary" "$probe/results/"
done
parent_make CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y wr-band-steering_clean \
  2>&1 | tee "$probe/results/clean.log"
test ! -e "$probe/trunk/user/wr-band-steering/build/wr-band-steering"
test ! -e "$probe/trunk/user/wr-band-steering/build/wr-band-steering-ctl"
parent_make CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y wr-band-steering_only \
  2>&1 | tee "$probe/results/rebuild.log"
for binary in wr-band-steering wr-band-steering-ctl; do
  cmp "$probe/results/$binary" "$probe/trunk/user/wr-band-steering/build/$binary"
done
