#!/usr/bin/env bash
# Isolated complete MT7603 WSC module, using reviewed wrapper Kbuild switches.
# Never changes the baseline kernel or installs this module in an image.
set -euo pipefail
kernel=$1
compiler=$2
results=$3
feature="$RUNNER_TEMP/wr1200js-iot-wsc-feature"
test ! -e "$feature"
mkdir -p "$results"
trap 'if [ -d "$feature" ]; then du -sh "$feature"; rm -rf -- "$feature"; fi' EXIT
cp -a "$kernel" "$feature"
driver="$feature/drivers/net/wireless/mediatek/mt76x3"
wrapper="$feature/drivers/net/wireless/mediatek/mt76x3_ap"
cross="${compiler%gcc}"
grep -Fq 'ifeq ($(CONFIG_MT7603E_WSC_INCLUDED),y)' "$wrapper/Makefile"
grep -Fq 'EXTRA_CFLAGS += -DWSC_INCLUDED -DWSC_SINGLE_TRIGGER' "$wrapper/Makefile"
sha256sum "$kernel/.config" > "$results/baseline-config.sha256"
cp "$feature/.config" "$results/kernel.config"
grep -qx 'CONFIG_MT7603E_RLT_AP_SUPPORT=m' "$feature/.config"
grep -qx 'CONFIG_MT76X3_AP=m' "$feature/.config"
# Command-line overrides select the wrapper's complete WSC object list.
# They are feature-build inputs, not a production .config change.
python3 tools/iot/prepare-wsc-apcli-probe.py "$driver" --report "$results/apcli-probe-source.json"
make -C "$feature" ARCH=mips CROSS_COMPILE="$cross" -j2 \
  M=drivers/net/wireless/mediatek/mt76x3_ap \
  CONFIG_MT7603E_WSC_INCLUDED=y CONFIG_MT7603E_WSC_V2_SUPPORT=y modules \
  2>&1 | tee "$results/build.log"
python3 tools/iot/check-task-config.py --kernel "$feature" --driver "$driver" \
  --compiler "$compiler" --output "$results/task-config.json"
module="$wrapper/mt76x3_ap.ko"
test -s "$module"
"${cross}readelf" -sW "$module" > "$results/symbols.txt"
for symbol in WscInit WscStop wr_iot_mbss_recovery_handoff; do
  awk -v name="$symbol" '$4 == "FUNC" && $7 != "UND" && $3 > 0 && $8 == name { found=1 } END { exit !found }' \
    "$results/symbols.txt"
done
cp "$module" "$results/mt76x3_ap-wsc.ko"
sha256sum -c "$results/baseline-config.sha256"
cmp "$feature/.config" "$results/kernel.config"
python3 - "$results" "$driver" <<'PY'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
driver=pathlib.Path(sys.argv[2])
task=json.loads((root/'task-config.json').read_text())
baseline_path=root.parent/'target-compile-result.json'
baseline=json.loads(baseline_path.read_text())
if (not baseline['target_compiled'] or baseline['production_installed'] or
        baseline['runtime_verified'] or
        baseline['task_source_sha256']!=task['source_sha256']):
    raise SystemExit('WSC feature source/baseline provenance mismatch')
required=('WSC_INCLUDED','WSC_AP_SUPPORT','WSC_V2_SUPPORT','KTHREAD_SUPPORT')
if task['status']!='complete' or not all(task['macros'].get(name) for name in required):
    raise SystemExit('Full WSC module lacks effective WSC compilation evidence')
data=(root/'mt76x3_ap-wsc.ko').read_bytes()
if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:
    raise SystemExit('Expected ELF32 little-endian MIPS WSC module')
objects={}
for name in ('wsc','wsc_tlv','wsc_ufd','wsc_v2','crypt_dh','crypt_biginteger'):
    obj=driver/'common'/(name+'.o')
    command=driver/'common'/('.'+name+'.o.cmd')
    blob=obj.read_bytes()
    if (blob[:6]!=b'\x7fELF\x01\x01' or
            int.from_bytes(blob[16:18],'little')!=1 or
            int.from_bytes(blob[18:20],'little')!=8):
        raise SystemExit('Expected MIPS relocatable WSC object: '+name)
    objects[name]={'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),
                   'command_sha256':hashlib.sha256(command.read_bytes()).hexdigest(),
                   'source_sha256':hashlib.sha256(obj.with_suffix('.c').read_bytes()).hexdigest()}
report={'scope':'complete isolated MT7603 WSC module',
        'repository_revision':baseline['repository_revision'],
        'source_revision':baseline['source_revision'],
        'baseline_module_sha256':baseline['module_sha256'],
        'baseline_report_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        'kernel_config_sha256':hashlib.sha256((root/'kernel.config').read_bytes()).hexdigest(),
        'make_overrides':{'CONFIG_MT7603E_WSC_INCLUDED':'y','CONFIG_MT7603E_WSC_V2_SUPPORT':'y'},
        'target_compiled':True,'production_installed':False,'runtime_verified':False,
        'module_bytes':len(data),'module_sha256':hashlib.sha256(data).hexdigest(),
        'task_macros':task['macros'],'task_command_sha256':task['command_sha256'],
        'task_source_sha256':task['source_sha256']}
report['wsc_objects']=objects
report['apcli_probe_source']=json.loads((root/'apcli-probe-source.json').read_text())
(root/'result.json').write_text(json.dumps(report,indent=2)+'\n')
PY
