#!/bin/bash
# Invoke from repository root after a successful normal WR1200JS firmware build.
set -euo pipefail
trunk="$(realpath "$1")"
probe="$2"
compiler="$(realpath "$3")"
test -s "$trunk/.config"
test -s "$trunk/config.arch"
test -s "$trunk/linux-4.4.x/.config"
test -s "$trunk/user/rc/rc"
test -x "$compiler"
test ! -e "$probe"
mkdir -p "$probe/trunk/user" "$probe/results"
cp -a "$trunk/user/rc" "$probe/trunk/user/rc"
probe="$(realpath "$probe")"
sha256sum "$trunk/.config" "$trunk/linux-4.4.x/.config" > "$probe/results/baseline-config.sha256"
python3 tools/band-steering/prepare-profile-integration.py "$probe"
python3 tools/band-steering/prepare-child-reaper.py "$probe"
python3 tools/band-steering/prepare-wifi-lifecycle.py "$probe"
python3 tools/band-steering/prepare-profile-snapshot.py "$probe"
python3 tools/band-steering/prepare-wifi-snapshot.py "$probe"
cross="${compiler%gcc}"
cat > "$probe/Makefile" <<'MAKE'
.DEFAULT_GOAL := wr-profile-probe
include $(ROOTDIR)/versions.inc
FIRMWARE_KERNEL_VER="4.4"
include $(ROOTDIR)/user/Makefile
.PHONY: wr-profile-probe
wr-profile-probe:
	$(MAKE) -C $(WR_PROBE_RC) clean
	$(MAKE) -C $(WR_PROBE_RC) -j2 all CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y
MAKE
make -f "$probe/Makefile" wr-profile-probe \
  ROOTDIR="$trunk" LINUXDIR=linux-4.4.x \
  PROJECT_CONFIG="$trunk/.config" LINUX_CONFIG="$trunk/linux-4.4.x/.config" \
  ARCH_CONFIG="$trunk/config.arch" WR_PROBE_RC="$probe/trunk/user/rc" \
  CC="$compiler" STRIP="${cross}strip" AR="${cross}ar" \
  2>&1 | tee "$probe/results/build.log"
rc="$probe/trunk/user/rc"
test -s "$rc/rc"
test -s "$rc/wr-band-profile-policy.o"
test -s "$rc/wr-band-lifecycle.o"
test -s "$rc/wr-band-service-owner.o"
test -s "$rc/wr-band-settings-snapshot.o"
grep -q -- '-DUSE_WR_BAND_STEERING_PROFILE' "$probe/results/build.log"
"${cross}nm" "$rc/wr-band-profile-policy.o" > "$probe/results/policy-symbols.txt"
grep -Eq '[[:space:]]wr_band_profile_from_settings$' "$probe/results/policy-symbols.txt"
"${cross}nm" "$rc/wr-band-lifecycle.o" > "$probe/results/lifecycle-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_lifecycle_apply$' "$probe/results/lifecycle-symbols.txt"
"${cross}nm" "$rc/wr-band-service-owner.o" > "$probe/results/service-owner-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_service_quiesce$' "$probe/results/service-owner-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_service_start$' "$probe/results/service-owner-symbols.txt"
"${cross}nm" "$rc/ralink.o" > "$probe/results/profile-io-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_generate_profiles$' "$probe/results/profile-io-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_profile_bind_snapshot$' "$probe/results/profile-io-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_profile_unbind_snapshot$' "$probe/results/profile-io-symbols.txt"
"${cross}nm" "$rc/net_wifi.o" > "$probe/results/wifi-lifecycle-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_band_apply_wifi_settings$' "$probe/results/wifi-lifecycle-symbols.txt"
grep -Eq '[[:space:]]U[[:space:]]nvram_getall$' "$probe/results/wifi-lifecycle-symbols.txt"
grep -Eq '[[:space:]]U[[:space:]]wr_band_profile_bind_snapshot$' "$probe/results/wifi-lifecycle-symbols.txt"
grep -Eq '[[:space:]]U[[:space:]]wr_band_snapshot_capture$' "$probe/results/wifi-lifecycle-symbols.txt"
"${cross}readelf" -h "$rc/rc" > "$probe/results/rc-elf.txt"
grep -q 'Machine:.*MIPS' "$probe/results/rc-elf.txt"
"${cross}readelf" -d "$rc/rc" > "$probe/results/rc-dependencies.txt"
cp "$rc/rc" "$rc/wr-band-profile-policy.o" "$probe/results/"
cp "$rc/wr-band-lifecycle.o" "$probe/results/"
cp "$rc/wr-band-service-owner.o" "$probe/results/"
cp "$rc/wr-band-settings-snapshot.o" "$probe/results/"
cp "$probe/band-steering-profile-snapshot.json" "$probe/results/"
cp "$probe/band-steering-profile-integration.json" "$probe/results/"
sha256sum "$probe/results/rc" > "$probe/results/rc.sha256"
sha256sum -c "$probe/results/baseline-config.sha256"

