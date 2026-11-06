#!/usr/bin/env bash
# Run from repository root with candidate inputs supplied through env.
set -euo pipefail
root="$RUNNER_TEMP/wr1200js-steering-driver-probe"
kernel="$root/trunk/linux-4.4.x"
driver="$kernel/drivers/net/wireless/mediatek/mt76x3"
pinned="$RUNNER_TEMP/wr1200js-iot-pinned"
candidate="$RUNNER_TEMP/wr1200js-iot-candidate"
merged="$RUNNER_TEMP/wr1200js-iot-merged-mt76x3"
results="$PWD/iot-merged-driver-results"
if [ "$CANDIDATE_SCOPE" = iot ]; then
  # The full Band Steering compile creates this tree only in 'all' scope.
  # Give an IoT-only run the same isolated, configured kernel baseline.
  test ! -e "$root"
  mkdir -p "$root/trunk" "$results"
  cp -a "$PWD/padavan-4.4/trunk/linux-4.4.x" "$kernel"
  python3 tools/band-steering/configure-driver-probe.py "$kernel"
  compiler="$(find "$PWD/padavan-4.4/toolchain/toolchain-mipsel" \
    -path '*/bin/mipsel-linux-uclibc-gcc' -print -quit)"
  test -n "$compiler"
  cross="${compiler%gcc}"
  make -C "$kernel" ARCH=mips CROSS_COMPILE="$cross" olddefconfig \
    2>&1 | tee "$results/config.log"
  grep -qx 'CONFIG_MT7603E_BAND_STEERING_7603=y' "$kernel/.config"
  grep -qx 'CONFIG_RT_BAND_STEERING=y' "$kernel/.config"
fi
if [ ! -d "$driver" ]; then
  echo '::error::Isolated IoT driver tree was not prepared' >&2
  exit 1
fi
test ! -e "$pinned" && test ! -e "$candidate" && test ! -e "$merged"
mkdir -p "$pinned" "$results"
test "$(git -C padavan-4.4 rev-parse HEAD)" = c25283e915a2a00a763774dd255b14aff997285e
git -C padavan-4.4 archive --format=tar HEAD \
  trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3 \
  | tar -xf - -C "$pinned"
pristine="$pinned/trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3"
python3 tools/iot/check-tx-power-builder.py "$pristine"
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  mkdir -p "$candidate"
  python3 tools/iot/prepare-current-recovery-chain.py "$pristine" "$candidate/recovery"
  python3 tools/iot/prepare-full-driver-overlay.py "$pristine" \
    "$candidate/recovery/later/corrected" \
    "$candidate/recovery/later/v24c-composition.json" "$candidate/full-driver"
  python3 tools/iot/prepare-peer-retirement-chain.py "$candidate/full-driver" "$candidate/peer"
  python3 tools/iot/assemble-peer-prepared-candidate.py "$pristine" "$driver" \
    "$candidate/peer/peer-chain.json" "$candidate/full-driver-overlay.json" "$merged"
  python3 tools/iot/prepare-terminal-command-lock-lifetime.py \
    "$merged" "$candidate/command-lifecycle"
  merged="$candidate/command-lifecycle"
  python3 tools/iot/prepare-ap-software-shutdown.py "$merged" "$candidate/ap-before-off"
  merged="$candidate/ap-before-off"
  python3 tools/iot/check-ap-before-radio-off.py "$merged"
  sender_parent="$merged"
  python3 tools/iot/prepare-mcu-sender-binding.py "$merged" "$candidate/mcu-sender"
  merged="$candidate/mcu-sender"
  python3 tools/iot/check-mcu-sender-binding.py "$sender_parent" "$merged"
  python3 tools/iot/prepare-mcu-result-check.py "$merged" "$results/checked-radio-result.c"
  gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
    -Itools/iot "$results/checked-radio-result.c" -o "$results/checked-radio-result"
  "$results/checked-radio-result"
  for fixture in check-mcu-sender-owner check-mcu-sender-wrapper check-mcu-sender-drain check-mcu-sender-release check-mcu-message-lifetime check-mcu-sequence-reservation; do
    gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
      -Itools/iot "tools/iot/$fixture.c" -o "$results/$fixture"
    "$results/$fixture"
  done
  python3 tools/iot/prepare-mcu-sequence-bound.py "$merged" "$candidate/sequence-bound"
  python3 tools/iot/check-mcu-sequence-bound.py "$candidate/sequence-bound"
  python3 tools/iot/prepare-mcu-sequence-reservation.py "$candidate/sequence-bound" "$candidate/sequence-reserved"
  merged="$candidate/sequence-reserved"
  # Counterexamples remain explicit; this also checks late timeout ACK rejection.
  python3 tools/iot/check-mcu-ack-epoch-gap.py "$merged"
  python3 tools/iot/prepare-mcu-init-rx-join.py "$merged" "$candidate/init-rx-joined"
  merged="$candidate/init-rx-joined"
  python3 tools/iot/check-mcu-init-rx-join.py "$merged"
  python3 tools/iot/prepare-wds-unregister-generation.py "$merged" "$candidate/wds-unregister-generation"
  merged="$candidate/wds-unregister-generation"
  python3 tools/iot/check-wds-unregister-generation.py "$merged"
  # Counterexample only: unregister does not retire raw RX readers.
  python3 tools/iot/check-wdev-unregister-reader-lifetime.py "$merged"
  python3 tools/iot/prepare-pci-netdev-preclose.py "$merged" "$candidate/pci-netdev-preclosed"
  merged="$candidate/pci-netdev-preclosed"
  python3 tools/iot/check-pci-netdev-preclose-binding.py "$merged"
  python3 tools/iot/prepare-mlme-checked-halt.py "$merged" "$candidate/mlme-checked-halt"
  merged="$candidate/mlme-checked-halt"
  python3 tools/iot/check-mlme-checked-halt.py "$merged"
  python3 tools/iot/prepare-mlme-timer-producer-join.py "$merged" "$candidate/mlme-timer-producer-joined"
  merged="$candidate/mlme-timer-producer-joined"
  python3 tools/iot/check-mlme-checked-halt.py "$merged"
  python3 tools/iot/prepare-main-reopen-fence.py "$merged" "$candidate/main-reopen-fenced"
  merged="$candidate/main-reopen-fenced"
  python3 tools/iot/check-main-reopen-fence.py "$merged"
  python3 tools/iot/prepare-main-recovery-rtnl-split.py "$merged" "$candidate/main-recovery-rtnl-split"
  merged="$candidate/main-recovery-rtnl-split"
  python3 tools/iot/check-main-recovery-rtnl-split.py "$merged"
  python3 tools/iot/prepare-main-physical-close-delegation.py "$merged" "$candidate/main-physical-close-delegated"
  merged="$candidate/main-physical-close-delegated"
  python3 tools/iot/check-main-physical-close-delegation.py "$merged"
  python3 tools/iot/prepare-mbss-owner-storage.py "$merged" "$candidate/mbss-owner-storage"
  merged="$candidate/mbss-owner-storage"
  python3 tools/iot/check-mbss-owner-storage.py "$merged"
  python3 tools/iot/check-main-reopen-fence.py "$merged"
  python3 tools/iot/prepare-raw-recovery-free-fence.py "$merged" "$candidate/raw-recovery-free-fenced"
  merged="$candidate/raw-recovery-free-fenced"
  python3 tools/iot/check-raw-recovery-free-fence.py "$merged"
  gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
    -Itools/iot tools/iot/check-pci-netdev-preclose.c -o "$results/check-pci-netdev-preclose"
  "$results/check-pci-netdev-preclose"
  gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
    -Itools/iot tools/iot/check-mcu-dma-disabled-idle.c -o "$results/check-mcu-dma-disabled-idle"
  "$results/check-mcu-dma-disabled-idle"
  python3 tools/iot/check-mcu-sequence-allocator.py "$merged"
  python3 tools/iot/check-mcu-sequence-release.py "$merged"
  python3 tools/iot/check-mcu-sequence-lifetime.py "$merged"
  python3 tools/iot/check-mcu-sequence-destructors.py "$merged"
  python3 tools/iot/check-command-lifecycle-calls.py "$merged"
  python3 tools/iot/check-retry-rtnl-header.py "$merged"
  python3 tools/iot/check-main-verify-module-macro.py "$merged"
  python3 tools/iot/check-joined-rearm.py "$merged"
  python3 tools/iot/check-radio-off-send.py "$merged"
  python3 tools/iot/check-agg-temp-lock.py "$merged"
  python3 tools/iot/check-tasklet-irq-rearm.py "$merged"
  python3 tools/iot/check-radio-on-retirement-admission.py "$merged"
  gcc -std=c11 -Wall -Wextra -Werror -O2 -fsanitize=address,undefined \
    -I"$merged/include" tools/iot/check-aux-family-retry-scheduler.c \
    -o "$results/check-aux-family-retry-scheduler"
  "$results/check-aux-family-retry-scheduler" | tee "$results/aux-family-retry-scheduler.txt"
  gcc -std=c11 -Wall -Wextra -Werror -O2 -fsanitize=address,undefined \
    -I"$merged/include" tools/iot/check-peer-rssi-delete.c -o "$results/check-peer-rssi-delete"
  "$results/check-peer-rssi-delete" | tee "$results/peer-rssi-delete.txt"
  # Apply MBSS work ownership only after the legacy host fixtures;
  # target Kbuild below consumes this final merged candidate.
  bash tools/iot/ci-prepare-mbss-caller.sh "$merged" "$candidate" "$results"
  merged="$candidate/mbss-poll-caller"
  cp "$candidate/peer/peer-chain.json" "$results/peer-chain.json"
elif [ "$IOT_CANDIDATE_VARIANT" = v39 ]; then
  mkdir -p "$candidate"
  cp -a tools/iot/candidates/aux-remove-close-v39 "$candidate/driver"
  cp tools/iot/candidates/aux-remove-close-v39/manifest.json "$candidate/manifest.json"
  python3 tools/iot/check-remove-result-abi.py "$candidate/driver"
elif [ "$IOT_CANDIDATE_VARIANT" = v40 ] ||
     [ "$IOT_CANDIDATE_VARIANT" = v41 ] ||
     [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
  mkdir -p "$candidate" .iot-local-check
  python3 tools/iot/check-mt7603-checked-off.py
  python3 tools/iot/check-mt7603-mac-stop-contract.py \
    tools/iot/candidates/aux-remove-close-v39 \
    --linux-header "$kernel/drivers/net/wireless/mediatek/mt76x3/include/os/rt_linux.h"
  python3 tools/iot/prepare-mt7603-checked-off-candidate.py \
    tools/iot/candidates/aux-remove-close-v39 \
    .iot-local-check/mt7603-radio-off-v40-ci \
    --linux-header "$kernel/drivers/net/wireless/mediatek/mt76x3/include/os/rt_linux.h"
  python3 tools/iot/check-radio-off-send.py \
    .iot-local-check/mt7603-radio-off-v40-ci
  if [ "$IOT_CANDIDATE_VARIANT" = v41 ] ||
     [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
    python3 tools/iot/prepare-mbss-checked-stop-candidate.py \
      .iot-local-check/mt7603-radio-off-v40-ci \
      .iot-local-check/mt7603-mbss-stop-v41-ci
    if [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
      python3 tools/iot/prepare-beacon-producer-candidate.py \
        .iot-local-check/mt7603-mbss-stop-v41-ci \
        .iot-local-check/mt7603-beacon-producer-v42-ci
      cp -a .iot-local-check/mt7603-beacon-producer-v42-ci "$candidate/driver"
      cp .iot-local-check/mt7603-beacon-producer-v42-ci.manifest.json \
        "$results/beacon-producer-binding.json"
    else
      cp -a .iot-local-check/mt7603-mbss-stop-v41-ci "$candidate/driver"
    fi
    cp .iot-local-check/mt7603-mbss-stop-v41-ci.manifest.json \
      "$results/mbss-stop-binding.json"
  else
    cp -a .iot-local-check/mt7603-radio-off-v40-ci "$candidate/driver"
  fi
  python3 tools/iot/prepare-dma-idle-check.py \
    "$candidate/driver/hw_ctrl/cmm_asic_mt.c" \
    "$RUNNER_TEMP/wr-iot-v40-dma-source.c" \
    "$RUNNER_TEMP/wr-iot-v40-dma-fixture.c"
  gcc -std=c11 -Wall -Wextra -Werror \
    "$RUNNER_TEMP/wr-iot-v40-dma-fixture.c" -o "$RUNNER_TEMP/wr-iot-v40-dma-fixture"
  "$RUNNER_TEMP/wr-iot-v40-dma-fixture"
  cmp tools/iot/virtual-open-claim.h "$candidate/driver/include/virtual-open-claim.h"
  cmp tools/iot/mt7603-main-observe.h "$candidate/driver/include/mt7603-main-observe.h"
  cp tools/iot/check-interface-reference.c "$RUNNER_TEMP/check-v40-reference.c"
  gcc -std=c11 -Wall -Wextra -Werror \
    -I "$candidate/driver/include" \
    "$RUNNER_TEMP/check-v40-reference.c" -o "$RUNNER_TEMP/check-v40-reference"
  "$RUNNER_TEMP/check-v40-reference"
  sed 's|"netdev-registration.inc"|"wr-iot-netdev-registration.inc"|' \
    tools/iot/check-netdev-registration.c > "$RUNNER_TEMP/check-v40-registration.c"
  gcc -std=c11 -Wall -Wextra -Werror \
    -I "$candidate/driver/include" \
    "$RUNNER_TEMP/check-v40-registration.c" -o "$RUNNER_TEMP/check-v40-registration"
  "$RUNNER_TEMP/check-v40-registration"
  gcc -std=c11 -Wall -Wextra -Werror -DWR_IOT_V40=1 \
    -I "$candidate/driver/include" -I tools/iot \
    tools/iot/check-mbss-post-open.c -o "$RUNNER_TEMP/wr-iot-mbss-post-open"
  "$RUNNER_TEMP/wr-iot-mbss-post-open"
  gcc -std=c11 -Wall -Wextra -Werror -DWR_IOT_V40=1 \
    -I "$candidate/driver/include" -I tools/iot \
    tools/iot/check-mbss-close.c -o "$RUNNER_TEMP/wr-iot-mbss-close-admission"
  "$RUNNER_TEMP/wr-iot-mbss-close-admission"
  gcc -std=c11 -Wall -Wextra -Werror -DWR_IOT_V40=1 \
    -DMT_MAC=1 \
    -I "$candidate/driver/include" -I tools/iot \
    tools/iot/check-mbss-close.c -o "$RUNNER_TEMP/wr-iot-mbss-close-mt"
  "$RUNNER_TEMP/wr-iot-mbss-close-mt"
  gcc -std=c11 -Wall -Wextra -Werror -DWR_IOT_V40=1 \
    -DMT_MAC=1 -DRTMP_PCI_SUPPORT=1 \
    -I "$candidate/driver/include" -I tools/iot \
    tools/iot/check-mbss-close.c -o "$RUNNER_TEMP/wr-iot-mbss-close-mt-pci"
  "$RUNNER_TEMP/wr-iot-mbss-close-mt-pci"
  gcc -std=c11 -Wall -Wextra -Werror -I tools/iot \
    tools/iot/check-mbss-close-recovery-owner.c \
    -o "$RUNNER_TEMP/wr-iot-mbss-close-recovery-owner"
  "$RUNNER_TEMP/wr-iot-mbss-close-recovery-owner"
  python3 tools/iot/check-virtual-if-call-coverage.py "$candidate/driver"
  expected_overlay_count=58
  if [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
    expected_overlay_count=60
  fi
  python3 tools/iot/prepare-v39-merge-manifest.py \
    "$pristine" "$candidate/driver" \
    tools/iot/candidates/aux-remove-close-v39/manifest.json \
    "$candidate/manifest.json" \
    --expected-overlay-count "$expected_overlay_count"
  python3 tools/iot/check-remove-result-abi.py "$candidate/driver"
elif [ "$IOT_CANDIDATE_VARIANT" = legacy ]; then
  python3 tools/iot/prepare-radio-queue-candidate.py "$pristine" "$candidate"
else
  echo 'Unsupported IoT candidate variant' >&2
  exit 1
fi
if [ "$IOT_CANDIDATE_VARIANT" != peer82 ]; then
  python3 tools/iot/check-overlay-conflicts.py \
    "$candidate/manifest.json" "$candidate/driver" "$driver" \
    --output "$results/prepared-overlap.json" \
    || test "$?" -eq 1
  python3 tools/iot/assemble-prepared-candidate.py \
    "$pristine" "$driver" "$candidate/driver" \
    "$candidate/manifest.json" "$merged"
fi
if [ "$IOT_CANDIDATE_VARIANT" = v39 ] ||
   [ "$IOT_CANDIDATE_VARIANT" = v40 ] ||
   [ "$IOT_CANDIDATE_VARIANT" = v41 ] ||
   [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
  python3 tools/iot/check-remove-result-abi.py "$merged"
fi
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  python3 tools/iot/prepare-fw-rom-ready.py "$merged"
  python3 tools/iot/check-fw-rom-ready.py "$merged"
  python3 tools/iot/prepare-mcu-owned-off.py "$merged"
  python3 tools/iot/check-mcu-owned-off.py --candidate "$merged"
  python3 tools/iot/prepare-close-ack-order.py "$merged" --install-isolated
  python3 tools/iot/check-close-ack-order.py "$merged"
  python3 tools/iot/check-staged-radio-off.py "$merged"
  python3 tools/iot/check-ap-resource-split.py "$merged/ap/ap.c"
  python3 tools/iot/check-nettask-data-lane.py "$merged"
  python3 tools/iot/check-ap-release-after-join.py --candidate "$merged"
  python3 tools/iot/prepare-mcu-boot-result.py "$merged" --install-isolated
  python3 tools/iot/check-mcu-boot-result.py "$merged"
  python3 tools/iot/check-mcu-scatter-result.py "$merged"
  python3 tools/iot/check-fw-method1.py "$merged"
  python3 tools/iot/check-mcu-rx-bounds.py "$merged"
  python3 tools/iot/check-ctrl-ring-reset.py "$merged"
  python3 tools/iot/prepare-mcu-rx-direct.py "$merged" --install-isolated
  python3 tools/iot/check-mcu-rx-direct.py "$merged"
  python3 tools/iot/check-mcu-rx-bounds.py "$merged"
  for layer in mcu-boot-transport mcu-boot-loader mcu-nettask-bootstrap \
    mcu-boot-open mcu-boot-freeze mcu-boot-rom-quiesce mcu-boot-pse-empty \
    mcu-boot-rx-discard mcu-boot-pse-drain mcu-boot-rx-refresh \
    mcu-boot-control-retire mcu-boot-ring-rearm mcu-boot-ring-transaction \
    mcu-checked-sequence-retirement mcu-boot-controller-init mcu-boot-rx-restart \
    mcu-boot-other-tx-idle mcu-boot-irq-prepare mcu-boot-dma-start \
    mcu-boot-irq-filter mcu-boot-irq-unmask mcu-boot-hardware \
    mcu-boot-rom-observe mcu-boot-retired-boundary mcu-boot-thaw \
    mcu-boot-loader-abort mcu-boot-loader-bind mcu-boot-scheduler \
    mcu-boot-scheduler-owner mcu-boot-scheduler-quota mcu-control-admission \
    mcu-command-admission mcu-boot-firmware-receipt mcu-sys-scheduler \
    mcu-post-fw-init mcu-boot-config-owner mcu-config-result mcu-config-transport \
    mcu-config-noresponse mcu-config-rf-pending mcu-config-rf-read \
    mcu-config-mac-pending mcu-config-mac-read mcu-config-ext mcu-config-timing \
    mcu-config-init-owner; do
    python3 "tools/iot/prepare-$layer.py" "$merged" --install-isolated
  done
  for fixture in mcu-boot-transport mcu-boot-builders mcu-nettask-bootstrap \
    mcu-boot-open mcu-boot-open-core mcu-boot-rom-quiesce mcu-boot-pse-empty \
    mcu-boot-rx-discard mcu-boot-pse-drain mcu-boot-rx-refresh \
    mcu-boot-control-retire mcu-boot-ring-rearm mcu-boot-ring-transaction \
    mcu-checked-sequence-retirement mcu-boot-controller-init mcu-boot-rx-restart \
    mcu-boot-other-tx-idle mcu-boot-irq-prepare mcu-boot-irq-owner \
    mcu-boot-dma-start mcu-boot-dma-owner mcu-boot-irq-filter \
    mcu-boot-irq-unmask mcu-boot-irq-unmask-owner mcu-boot-hardware \
    mcu-boot-rom-observe mcu-boot-retired-boundary mcu-boot-thaw \
    mcu-boot-loader-abort mcu-boot-scheduler mcu-boot-scheduler-owner mcu-boot-sdk-quota \
    fw-method1 mcu-rx-bounds mcu-control-wrappers mcu-command-admission \
    mcu-wsc-gpio-path mcu-boot-firmware-receipt mcu-sys-scheduler \
    mcu-post-fw-init mcu-boot-config-owner mcu-config-result mcu-rx-direct \
    mcu-config-transport mcu-config-rf-pending; do
    python3 "tools/iot/check-$fixture.py" "$merged"
  done
  python3 tools/iot/check-mcu-config-init-owner.py "$merged"
  for fixture in allocator release lifetime destructors; do
    python3 "tools/iot/check-mcu-sequence-$fixture.py" "$merged"
  done
  python3 tools/iot/check-mcu-ack-epoch-gap.py "$merged"
fi
cp "$merged.manifest.json" "$results/merged-source-manifest.json"
cp -a "$merged/." "$driver/"
python3 - "$results/merged-source-manifest.json" "$driver" <<'PY'
import hashlib, json, pathlib, sys
manifest = json.load(open(sys.argv[1], encoding='utf-8'))
driver = pathlib.Path(sys.argv[2])
if manifest['target_compiled'] or manifest['production_installed']:
    raise SystemExit('Candidate manifest makes an unsupported claim')
for name, expected in manifest['candidate_driver_sha256'].items():
    path = driver / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Isolated source copy mismatch: ' + name)
    path.touch()
PY
python3 tools/iot/check_mbss_cr_enable.py "$driver/ap/ap_mbss_inf.c" \
  --compiler "$(command -v gcc)"
compiler="$(find "$PWD/padavan-4.4/toolchain/toolchain-mipsel" \
  -path '*/bin/mipsel-linux-uclibc-gcc' -print -quit)"
test -n "$compiler"
cross="${compiler%gcc}"
sha256sum "$kernel/.config" > "$results/config-before.sha256"
# Preserve actual inputs even if Kbuild fails before the success report.
cp "$kernel/.config" "$results/kernel-before.config"
header_dirs=()
for directory in include/generated include/config arch/mips/include/generated; do
  if [ -d "$kernel/$directory" ]; then header_dirs+=("$directory"); fi
done
if [ "${#header_dirs[@]}" -gt 0 ]; then
  tar -czf "$results/kernel-generated-headers.tar.gz" -C "$kernel" "${header_dirs[@]}"
fi
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  "$compiler" -std=c11 -Wall -Wextra -Werror -O2 -mips32r2 -mabi=32 -msoft-float \
    -I"$driver/include" -c tools/iot/check-peer-rssi-delete.c \
    -o "$results/peer-rssi-delete-mips.o"
fi
make -C "$kernel" ARCH=mips CROSS_COMPILE="$cross" -j2 vmlinux modules \
  2>&1 | tee "$results/build.log"
cmp tools/iot/mt7603-main-observe.h "$driver/include/mt7603-main-observe.h"
# Record actual rt_linux TU macros from the merged candidate Kbuild.
python3 tools/iot/check-task-config.py \
  --kernel "$kernel" --driver "$driver" --compiler "$compiler" \
  --output "$results/merged-task-config.json"
python3 tools/iot/check-task-config.py \
  --kernel "$kernel" --driver "$driver" --compiler "$compiler" \
  --unit rt_rbus_pci_drv --output "$results/merged-nettask-config.json"
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  python3 tools/iot/check-mlme-wsc-target-tu.py \
    --kernel "$kernel" --driver "$driver" --compiler "$compiler" \
    --output "$results/mlme-wsc-target-tu.json"
  python3 tools/iot/check-radio-off-reload-target-tu.py \
    --kernel "$kernel" --driver "$driver" --compiler "$compiler" \
    --output "$results/radio-off-reload-target-tu.json"
fi
python3 tools/iot/check-capacity.py "$kernel" mt76x3 \
  --compiler "$compiler" --require-three-bss --check-main-observer \
  --source-commit c25283e915a2a00a763774dd255b14aff997285e \
  --output "$results/merged-capacity.json"
python3 - "$results/merged-capacity.json" "$IOT_CANDIDATE_VARIANT" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding='utf-8'))
variant = sys.argv[2]
if report['main_observer_probe']['status'] != 'compiled':
    raise SystemExit('MT7603 main observer target compilation missing')
lock = report['beacon_lock_units_probe']
units = lock['units']
if len(units) != 9 or not lock['all_unit_flags_available'] or not lock['all_site_activity_available']:
    raise SystemExit('Incomplete per-unit beacon lock Kbuild evidence')
# The reviewed TIM admission overlay adds one active SEM site in ap_nps.c.
site_count = sum(len(unit['sites']) for unit in units.values())
active = [site for unit in units.values() for site in unit['sites']
          if site['active_after_directives']]
sem_count = sum(site['form'] == 'SEM' for site in active)
irq_count = sum(site['form'] == 'IRQ' for site in active)
# This inventory scans unit source text, not v42's new inline
# helper header. v42 replaces the abort-open SEM site with a gated
# helper; its header is checked by manifest and target compile.
expected = (20, 19, 10, 9) if variant in ('v42', 'peer82') else (21, 20, 11, 9)
if (site_count, len(active), sem_count, irq_count) != expected:
    raise SystemExit('Merged candidate active beacon lock forms changed')
# Both forms use the BH wrapper only while MULTI_CORE_SUPPORT is off.
# This guards the reviewed target build, not callback/lifetime safety.
if any(unit['effective_multi_core_support'] for unit in units.values()):
    raise SystemExit('Mixed beacon lock forms with MULTI_CORE_SUPPORT')
PY
module="$kernel/drivers/net/wireless/mediatek/mt76x3_ap/mt76x3_ap.ko"
test -s "$module"
"${cross}readelf" -h "$module" > "$results/mt76x3-elf.txt"
grep -q 'Machine:.*MIPS' "$results/mt76x3-elf.txt"
"${cross}readelf" -sW "$module" > "$results/mt76x3-symbols.txt"
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  for symbol in wr_iot_aux_family_retry_work_fn wr_rssi_delete_entry \
    wr_iot_mbss_begin_close wr_iot_mbss_close_checked \
    wr_iot_mbss_recovery_work_fn wr_iot_mbss_recovery_join_completed \
    wr_iot_mbss_recovery_stop_join wr_iot_mbss_recovery_submit \
    wr_iot_mbss_recovery_submit_close wr_iot_mbss_recovery_retry \
    wr_iot_mbss_recovery_poll wr_iot_mbss_poll_schedule \
    wr_iot_mbss_poll_work_fn wr_iot_mbss_poll_join \
    wr_iot_mbss_poll_stop_join wr_iot_mbss_recovery_handoff wr_iot_mcu_send_owned_off \
    wr_iot_mt_prepare_close_rx wr_iot_nettask_data_exit wr_iot_ap_release_after_join \
    wr_iot_mcu_checked_rx_packet wr_iot_mcu_boot_reserve wr_iot_mcu_boot_alloc \
    wr_iot_mcu_boot_send wr_iot_mcu_boot_rom_quiesce wr_iot_mcu_boot_rx_refresh \
    wr_iot_mcu_boot_control_retire wr_iot_mcu_boot_ring_rearm \
    wr_iot_mcu_boot_ring_transaction wr_iot_mcu_boot_controller_init \
    wr_iot_mcu_boot_rx_restart wr_iot_mcu_boot_other_tx_idle \
    wr_iot_mcu_boot_irq_prepare wr_iot_mcu_boot_dma_start \
    wr_iot_mcu_boot_dma_start_hw wr_iot_mcu_boot_dma_stop_hw; do
    awk -v name="$symbol" '$4 == "FUNC" && $7 != "UND" && $3 > 0 && $8 == name { found=1 } END { exit !found }' \
      "$results/mt76x3-symbols.txt"
  done
fi
if [ "$IOT_CANDIDATE_VARIANT" = v40 ] ||
   [ "$IOT_CANDIDATE_VARIANT" = v41 ] ||
   [ "$IOT_CANDIDATE_VARIANT" = v42 ]; then
  for symbol in wr_iot_mbss_begin_close wr_iot_mbss_close_checked wr_iot_virtual_down_checked; do
    awk -v name="$symbol" '$4 == "FUNC" && $7 != "UND" && $3 > 0 && $8 == name { found=1 } END { exit !found }' \
      "$results/mt76x3-symbols.txt"
  done
fi
cp "$module" "$results/"
python3 tools/iot/check-radio-off-module.py "$module" "$results/radio-off-capability.json" --cross "$cross"
cp "$kernel/.config" "$results/kernel.config"
sha256sum -c "$results/config-before.sha256"
python3 - "$results" "$IOT_CANDIDATE_VARIANT" "$CANDIDATE_SHA" <<'PY'
import hashlib, json, pathlib, re, sys
results = pathlib.Path(sys.argv[1])
source = json.loads((results / 'merged-source-manifest.json').read_text(encoding='utf-8'))
module = results / 'mt76x3_ap.ko'
task = json.loads((results / 'merged-task-config.json').read_text(encoding='utf-8'))
nettask = json.loads((results / 'merged-nettask-config.json').read_text(encoding='utf-8'))
if nettask['status'] != 'complete':
    raise SystemExit('Merged RX nettask configuration evidence missing')
if sys.argv[2] == 'peer82':
    required_rx = ('MT_MAC', 'CONFIG_ANDES_SUPPORT', 'RTMP_PCI_SUPPORT')
    missing_rx = [name for name in required_rx if not nettask['macros'].get(name)]
    if missing_rx:
        raise SystemExit('Peer82 RX evidence lacks required MT7603 PCI path: '
                         + ', '.join(missing_rx))
if task['status'] != 'complete':
    raise SystemExit('Merged rt_linux task configuration evidence missing')
elf = (results / 'mt76x3-elf.txt').read_text(encoding='utf-8')
if source['target_compiled'] or source['production_installed'] or not module.is_file():
    raise SystemExit('Invalid isolated IoT source/build boundary')
if not re.search(r'^\s*Machine:\s+MIPS\b', elf, re.MULTILINE):
    raise SystemExit('Isolated IoT module is not MIPS ELF')
report = {
    'schema': 1,
    'candidate_variant': sys.argv[2],
    'repository_revision': sys.argv[3],
    'source_revision': source['source_revision'],
    'target_compiled': True,
    'production_installed': False,
    'runtime_verified': False,
    'module': 'mt76x3_ap.ko',
    'module_bytes': module.stat().st_size,
    'module_sha256': hashlib.sha256(module.read_bytes()).hexdigest(),
    'compiled_task_macros': task['macros'],
    'compiled_nettask_macros': nettask['macros'],
    'nettask_command_sha256': nettask['command_sha256'],
    'nettask_source_sha256': nettask['source_sha256'],
    'task_command_sha256': task['command_sha256'],
    'task_source_sha256': task['source_sha256'],
}
(results / 'target-compile-result.json').write_text(
    json.dumps(report, indent=2) + '\n', encoding='utf-8')
PY
if [ "$IOT_CANDIDATE_VARIANT" = peer82 ]; then
  bash tools/iot/ci-compile-wsc-feature.sh "$kernel" "$compiler" "$results/wsc-feature"
  bash tools/iot/ci-compile-reload-feature.sh "$kernel" "$compiler" "$results/reload-feature"
fi
