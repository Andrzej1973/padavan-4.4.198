#!/usr/bin/env bash
# Complete isolated reload profile. Never install or change production config.
set -euo pipefail
kernel=$1
compiler=$2
results=$3
feature="$RUNNER_TEMP/wr1200js-iot-reload-feature"
test ! -e "$feature"
mkdir -p "$results"
trap 'if [ -d "$feature" ]; then du -sh "$feature"; rm -rf -- "$feature"; fi' EXIT
cp -a "$kernel" "$feature"
driver="$feature/drivers/net/wireless/mediatek/mt76x3"
wrapper="$feature/drivers/net/wireless/mediatek/mt76x3_ap"
cross="${compiler%gcc}"
python3 - "$wrapper/Makefile" "$results/wrapper-source.json" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]); before=p.read_bytes()
if hashlib.sha256(before).hexdigest()!='4c51b2a7a474c1e081a369562ca8ce28a80e0485a675723335b3106a347141c5':
    raise SystemExit('Unreviewed MT7603 wrapper')
old=b'EXTRA_CFLAGS += -DLOAD_FW_ONE_TIME'
if before.count(old)!=2: raise SystemExit('Expected two one-time firmware flags')
after=before.replace(old,b'# Isolated reload feature: LOAD_FW_ONE_TIME omitted')
p.write_bytes(after)
pathlib.Path(sys.argv[2]).write_text(json.dumps({
    'input_sha256':hashlib.sha256(before).hexdigest(),
    'output_sha256':hashlib.sha256(after).hexdigest(),
    'removed_flags':2},indent=2)+'\n')
PY
cp "$kernel/.config" "$results/kernel.config"
make -C "$feature" ARCH=mips CROSS_COMPILE="$cross" -j2 \
  M=drivers/net/wireless/mediatek/mt76x3_ap modules 2>&1 | tee "$results/build.log"
for unit in rt_linux rt_rbus_pci_drv andes_mt cmm_asic_mt cmm_mac_pci cmm_data; do
  python3 tools/iot/check-task-config.py --kernel "$feature" --driver "$driver" \
    --compiler "$compiler" --unit "$unit" --output "$results/$unit-config.json"
done
module="$wrapper/mt76x3_ap.ko"
test -s "$module"
cp "$module" "$results/mt76x3_ap-reload.ko"
python3 tools/iot/check-radio-off-module.py "$module" "$results/radio-off-capability.json" --cross "$cross"
cmp "$kernel/.config" "$results/kernel.config"
cmp "$feature/.config" "$results/kernel.config"
python3 - "$results" <<'PY'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); reports={}
source_manifest=json.loads((root.parent/'merged-source-manifest.json').read_text())
paths={'rt_linux':'os/linux/rt_linux.c','rt_rbus_pci_drv':'os/linux/rt_rbus_pci_drv.c',
       'andes_mt':'mcu/andes_mt.c','cmm_asic_mt':'hw_ctrl/cmm_asic_mt.c','cmm_mac_pci':'common/cmm_mac_pci.c','cmm_data':'common/cmm_data.c'}
for unit in ('rt_linux','rt_rbus_pci_drv','andes_mt','cmm_asic_mt','cmm_mac_pci','cmm_data'):
    report=json.loads((root/(unit+'-config.json')).read_text())
    macros=report['macros']
    if (report['status']!='complete' or macros['LOAD_FW_ONE_TIME'] or
        not macros['MT_MAC'] or not macros['RTMP_PCI_SUPPORT']):
        raise SystemExit('Reload profile macro mismatch: '+unit)
    if unit=='cmm_mac_pci' and not macros['RESOURCE_PRE_ALLOC']:
        raise SystemExit('Expected verified preallocated ring reset path')
    if report['source_sha256']!=source_manifest['merged_driver_sha256'][paths[unit]]:
        raise SystemExit('Reload source differs from the candidate: '+unit)
    reports[unit]=report
cap=json.loads((root/'radio-off-capability.json').read_text())
if cap['known_unconditional_false'] or cap['symbol_bytes']<=8:
    raise SystemExit('Reload module retained the checked-off refusal stub')
baseline_path=root.parent/'target-compile-result.json'
baseline=json.loads(baseline_path.read_text())
if not baseline['target_compiled'] or baseline['production_installed']:
    raise SystemExit('Invalid baseline')
data=(root/'mt76x3_ap-reload.ko').read_bytes()
if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:
    raise SystemExit('Expected little-endian MIPS module')
report={'scope':'complete isolated MT7603 reload module',
        'repository_revision':baseline['repository_revision'],
        'source_revision':baseline['source_revision'],
        'baseline_report_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        'kernel_config_sha256':hashlib.sha256((root/'kernel.config').read_bytes()).hexdigest(),
        'module_bytes':len(data),'module_sha256':hashlib.sha256(data).hexdigest(),
        'wrapper':json.loads((root/'wrapper-source.json').read_text()),
        'translation_units':reports,'target_compiled':True,
        'production_installed':False,'firmware_epoch_verified':False,
        'shutdown_verified':False,'runtime_verified':False}
(root/'result.json').write_text(json.dumps(report,indent=2)+'\n')
PY
