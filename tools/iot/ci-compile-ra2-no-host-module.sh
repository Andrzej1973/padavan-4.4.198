#!/usr/bin/env bash
# Link the experimental driver in an isolated kernel copy on GitHub Actions.
set -euo pipefail
kernel=$1
compiler=$2
experiment=$3
results=$4
feature="$RUNNER_TEMP/wr1200js-ra2-no-host-module"
test ! -e "$feature"
mkdir -p "$results"
trap 'if [ -d "$feature" ]; then du -sh "$feature"; rm -rf -- "$feature"; fi' EXIT
cp -a "$kernel" "$feature"
driver="$feature/drivers/net/wireless/mediatek/mt76x3"
wrapper="$feature/drivers/net/wireless/mediatek/mt76x3_ap"
cp "$feature/.config" "$results/kernel.config"
python3 - "$experiment" "$driver" "$results" <<'PY'
import hashlib,json,shutil,sys
from pathlib import Path
source,driver,results=map(Path,sys.argv[1:])
manifest=json.loads(Path(str(source)+'.manifest.json').read_text())
metadata=manifest['ra2_no_host_experiment']
if metadata['activation_ready'] is not False or manifest['production_installed'] is not False:
    raise SystemExit('Expected compile-only experiment')
for name,expected in manifest['candidate_driver_sha256'].items():
    if hashlib.sha256((source/name).read_bytes()).hexdigest()!=expected:
        raise SystemExit('Experiment input drift: '+name)
for name in metadata['changed_paths']:
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise SystemExit('Invalid experiment path')
    target=driver/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source/name,target)
    target.touch()
    if hashlib.sha256(target.read_bytes()).hexdigest()!=manifest['candidate_driver_sha256'][name]:
        raise SystemExit('Experimental source copy mismatch')
(results/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
PY
cross="${compiler%gcc}"
make -C "$feature" ARCH=mips CROSS_COMPILE="$cross" -j2 \
  M=drivers/net/wireless/mediatek/mt76x3_ap modules \
  2>&1 | tee "$results/build.log"
cp "$wrapper/mt76x3_ap.ko" "$results/mt76x3_ap-ra2-no-host.ko"
"${cross}readelf" -h "$results/mt76x3_ap-ra2-no-host.ko" > "$results/elf.txt"
"${cross}readelf" -sW "$results/mt76x3_ap-ra2-no-host.ko" > "$results/symbols.txt"
for symbol in APUpdateBeaconFrame BcnTxSHandler RT28xx_UpdateBeaconToAsic; do
  awk -v name="$symbol" '$4 == "FUNC" && $7 != "UND" && $3 > 0 && $8 == name { found=1 } END { exit !found }' "$results/symbols.txt"
done
cmp "$feature/.config" "$results/kernel.config"
python3 - "$results" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1])
blob=(root/'mt76x3_ap-ra2-no-host.ko').read_bytes()
if blob[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(blob[18:20],'little')!=8:
    raise SystemExit('Expected ELF32 little-endian MIPS module')
report={'target_module_linked':True,'module_bytes':len(blob),
        'module_sha256':hashlib.sha256(blob).hexdigest(),
        'production_installed':False,'activation_ready':False,'runtime_verified':False}
(root/'target-result.json').write_text(json.dumps(report,indent=2)+'\n')
PY
