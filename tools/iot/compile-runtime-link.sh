#!/usr/bin/env bash
# Run after normal firmware succeeds; never install this experimental candidate.
set -euo pipefail
trunk="$(realpath "$1")"
compiler="$(realpath "$2")"
results="$(realpath -m "$3")"
for path in .config config.arch linux-4.4.x/.config user/rc/rc user/httpd/httpd; do
  test -s "$trunk/$path"
done
test -x "$compiler"
test ! -e "$results"
mkdir -p "$results"
probe="$(mktemp -d "$RUNNER_TEMP/iot-runtime-link.XXXXXX")"
trap 'find "$probe" -depth -delete' EXIT
mkdir -p "$probe/trunk/user" "$probe/trunk/configs/boards/WR1200JS"
cp -a "$trunk/user/rc" "$trunk/user/httpd" "$probe/trunk/user/"
cp "$trunk/configs/boards/WR1200JS/l1profile.dat" "$probe/trunk/configs/boards/WR1200JS/"
sha256sum "$trunk/.config" "$trunk/config.arch" "$trunk/linux-4.4.x/.config" \
  "$trunk/user/rc/rc" "$trunk/user/httpd/httpd" > "$results/baseline.sha256"
for stage in rc http control runtime; do
  python3 "tools/iot/prepare-$stage.py" "$probe"
done
python3 tools/iot/check-runtime-source.py "$probe" "$probe/source-check"
cross="${compiler%gcc}"
cat > "$probe/Makefile" <<'MAKE'
.DEFAULT_GOAL := iot-runtime-link
include $(ROOTDIR)/versions.inc
FIRMWARE_KERNEL_VER="4.4"
include $(ROOTDIR)/user/Makefile
.PHONY: iot-runtime-link
iot-runtime-link:
	$(MAKE) -C $(IOT_PROBE)/trunk/user/rc clean
	$(MAKE) -C $(IOT_PROBE)/trunk/user/httpd clean
	$(MAKE) -C $(IOT_PROBE)/trunk/user/rc -j2 all
	$(MAKE) -C $(IOT_PROBE)/trunk/user/httpd -j2 all
MAKE
make -f "$probe/Makefile" iot-runtime-link ROOTDIR="$trunk" LINUXDIR=linux-4.4.x \
  PROJECT_CONFIG="$trunk/.config" LINUX_CONFIG="$trunk/linux-4.4.x/.config" \
  ARCH_CONFIG="$trunk/config.arch" IOT_PROBE="$probe" \
  CC="$compiler" STRIP="${cross}strip" AR="${cross}ar" \
  2>&1 | tee "$results/build.log"
"${cross}nm" "$probe/trunk/user/rc/wr-iot-rc-backend.o" > "$results/backend-symbols.txt"
for symbol in wr_iot_activation_execute wr_iot_activation_continue wr_iot_rc_backend_observed wr_iot_activation_prepare_radio_stop wr_iot_rc_quiesce_begin wr_iot_rc_quiesce_advance; do
  grep -Eq "[[:space:]]T[[:space:]]$symbol\$" "$results/backend-symbols.txt"
done
for entry in physical-stop-client:wr_iot_physical_stop_call physical-stop-down:wr_iot_physical_stop_down physical-stop-session:wr_iot_physical_session_begin physical-stop-session:wr_iot_physical_session_advance rc-physical-stop:wr_iot_rc_physical_begin rc-physical-stop:wr_iot_rc_physical_step rc-physical-stop:wr_iot_rc_physical_restart_ready rc-physical-stop:wr_iot_rc_physical_begin_quiesce rc-physical-stop:wr_iot_rc_physical_resume_read physical-rebind-client:wr_iot_physical_rebind_call physical-rebind-controller:wr_iot_rebind_open_submit physical-rebind-controller:wr_iot_rebind_open_current physical-rebind-controller:wr_iot_rebind_configuration_current rebind-start:wr_iot_rebind_start_begin rebind-network:wr_iot_rebind_network_step rebind-rollback:wr_iot_rebind_rollback_step rebind-commit:wr_iot_rebind_commit_step rebind-close:wr_iot_rebind_close_step rebind-closed-rollback:wr_iot_rebind_closed_rollback_step rebind-runner:wr_iot_rebind_runner_begin rebind-runner:wr_iot_rebind_runner_continue; do
  unit="${entry%%:*}"
  symbol="${entry#*:}"
  "${cross}nm" "$probe/trunk/user/rc/wr-iot-$unit.o" > "$results/$unit-symbols.txt"
  grep -Eq "[[:space:]]T[[:space:]]$symbol\$" "$results/$unit-symbols.txt"
done
"${cross}nm" "$probe/trunk/user/rc/net_wifi.o" > "$results/physical-aux-symbols.txt"
grep -Eq '[[:space:]]T[[:space:]]wr_iot_rc_physical_aux_down$' "$results/physical-aux-symbols.txt"
mkdir -p "$probe/staged/usr/sbin"
for role in rc httpd; do
  binary="$probe/trunk/user/$role/$role"
  test -s "$binary"
  "${cross}readelf" -h "$binary" > "$results/$role-elf.txt"
  grep -q 'Machine:.*MIPS' "$results/$role-elf.txt"
  "${cross}readelf" -Ws "$binary" > "$results/$role-symbols.txt"
  if grep -Eq 'UND[[:space:]]+wr_iot_' "$results/$role-symbols.txt"; then
    echo "Unresolved IoT symbol in $role" >&2; exit 1
  fi
  cp "$binary" "$results/$role"
  cp "$binary" "$probe/staged/usr/sbin/$role"
  python3 tools/band-steering/verify-package-closure.py "$probe/staged" "$trunk/romfs" \
    --binary "usr/sbin/$role" --readelf "${cross}readelf" \
    --output "$results/$role-dependency-closure.json"
done
cp "$probe/iot-runtime-source.json" "$results/"
sha256sum "$results/rc" "$results/httpd" > "$results/candidate.sha256"
sha256sum -c "$results/baseline.sha256"
printf '%s\n' 'PASS experimental RC/HTTP target link and dependency closure; no image installation or physical acceptance'
