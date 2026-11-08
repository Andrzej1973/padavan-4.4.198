#!/usr/bin/env bash
# Full opt-in diagnostic module A/B builds; never install in production image.
set -euo pipefail
python3 tools/iot/check-psm-diagnostics.py
python3 tools/iot/check-psm-build-report.py
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
  mkdir "$results/commands-$mode" "$results/objects-$mode"
  for unit in common/mt_ps ap/ap ap/ap_connect tx_rx/txs; do
    cp "$driver/${unit%/*}/.${unit##*/}.o.cmd" "$results/commands-$mode/${unit##*/}.cmd"
    cp "$driver/$unit.o" "$results/objects-$mode/${unit##*/}.o"
  done
  cmp "$feature/.config" "$results/kernel.config"
done
python3 - "$results" "$driver" <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path(sys.argv[1]);driver=Path(sys.argv[2]);out={'target_compiled':True,'production_installed':False,'runtime_verified':False,'variants':{}}
for mode in ['off','on']:
 data=(r/f'mt76x3_ap-psm-{mode}.ko').read_bytes()
 assert data[:6]==b'\x7fELF\x01\x01' and int.from_bytes(data[18:20],'little')==8
 objects={}
 commands=list((r/f'commands-{mode}').glob('*.cmd'))
 assert {p.stem for p in commands}=={'mt_ps','ap','ap_connect','txs'}
 for cmd in commands:
  # Test the actual compiler command, not its dependency/include text.
  compile_lines=[line for line in cmd.read_text().splitlines() if line.startswith('cmd_') and ':=' in line]
  assert len(compile_lines)==1
  assert ('-DWR_IOT_PSM_DIAG' in compile_lines[0].split())==(mode=='on')
  obj=(r/f'objects-{mode}'/(cmd.stem+'.o')).read_bytes()
  assert obj[:6]==b'\x7fELF\x01\x01' and int.from_bytes(obj[18:20],'little')==8
  objects[cmd.stem]={'object_sha256':hashlib.sha256(obj).hexdigest(),'command_sha256':hashlib.sha256(cmd.read_bytes()).hexdigest()}

 out['variants'][mode]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'objects':objects}
assert out['variants']['off']['sha256']!=out['variants']['on']['sha256']
out['source_sha256']={name:hashlib.sha256((driver/name).read_bytes()).hexdigest() for name in
 ['common/mt_ps.c','ap/ap.c','ap/ap_connect.c','tx_rx/txs.c','include/wr-iot-psm-diag.h']}
(r/'target-result.json').write_text(json.dumps(out,indent=2)+'\n')
PY
