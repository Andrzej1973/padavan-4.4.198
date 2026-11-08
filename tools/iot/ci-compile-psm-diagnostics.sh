#!/usr/bin/env bash
# Full opt-in diagnostic module A/B builds; never install in production image.
set -euo pipefail
python3 tools/iot/check-psm-diagnostics.py
kernel=$1
compiler=$2
results=$3
feature="$RUNNER_TEMP/wr1200js-psm-diagnostic-feature"
test ! -e "$feature"
mkdir -p "$results"
trap 'if [ -d "$feature" ]; then du -sh "$feature"; rm -rf -- "$feature"; fi' EXIT
cp -a "$kernel" "$feature"
driver="$feature/drivers/net/wireless/mediatek/mt76x3"
wrapper="$feature/drivers/net/wireless/mediatek/mt76x3_ap"
cross="${compiler%gcc}"
python3 tools/iot/prepare-psm-diagnostics.py "$driver" "$results/diagnostics.patch"
# Use absolute path also when result directory was supplied relative to checkout.
patch_path="$(realpath "$results/diagnostics.patch")"
(cd "$driver" && git apply --check "$patch_path" && git apply "$patch_path")
cp "$wrapper/Makefile" "$results/wrapper.Makefile.before"
cp "$feature/.config" "$results/kernel.config"
for mode in off on; do
  cp "$results/wrapper.Makefile.before" "$wrapper/Makefile"
  if [ "$mode" = on ]; then
    printf '\nEXTRA_CFLAGS += -DWR_IOT_PSM_DIAG\n' >> "$wrapper/Makefile"
  fi
  make -C "$feature" ARCH=mips CROSS_COMPILE="$cross" -j2 \
    M=drivers/net/wireless/mediatek/mt76x3_ap modules \
    2>&1 | tee "$results/build-$mode.log"
  cp "$wrapper/mt76x3_ap.ko" "$results/mt76x3_ap-psm-$mode.ko"
  "${cross}readelf" -h "$results/mt76x3_ap-psm-$mode.ko" > "$results/elf-$mode.txt"
  "${cross}strings" "$results/mt76x3_ap-psm-$mode.ko" > "$results/strings-$mode.txt"
  if [ "$mode" = off ]; then
    if grep -Fq 'wr_ps event=' "$results/strings-$mode.txt"; then exit 1; fi
  else
    grep -Fq 'wr_ps event=' "$results/strings-$mode.txt"
  fi
  mkdir "$results/commands-$mode"
  for unit in common/mt_ps ap/ap ap/ap_connect tx_rx/txs; do
    cp "$driver/${unit%/*}/.${unit##*/}.o.cmd" "$results/commands-$mode/${unit##*/}.cmd"
  done
  cmp "$feature/.config" "$results/kernel.config"
done
python3 - "$results" <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path(sys.argv[1]);out={'target_compiled':True,'production_installed':False,'runtime_verified':False,'variants':{}}
for mode in ['off','on']:
 data=(r/f'mt76x3_ap-psm-{mode}.ko').read_bytes()
 assert data[:6]==b'\x7fELF\x01\x01' and int.from_bytes(data[18:20],'little')==8
 for cmd in (r/f'commands-{mode}').glob('*.cmd'):
  assert ('-DWR_IOT_PSM_DIAG' in cmd.read_text())==(mode=='on')
 out['variants'][mode]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(r/'target-result.json').write_text(json.dumps(out,indent=2)+'\n')
PY
