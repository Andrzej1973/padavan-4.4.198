#!/usr/bin/env bash
# Isolated GitHub-only ROMFS staging. Does not publish a flashable image.
set -euo pipefail
trunk="$(realpath "$1")"
results="$(realpath "$2")"
compiler="$(realpath "$3")"
revision="$4"
test -d "$trunk/romfs"
test -x "$compiler"
test -s "$results/paired-image-inputs.json"
python3 - <<'PY'
import runpy
from pathlib import Path
validate=runpy.run_path('tools/iot/verify-board-layout.py')['validate_wr_layout']
layout=validate(Path.cwd())
print('PASS WR1200JS layout/image-size contract:',layout['firmware'])
PY
probe="$(mktemp -d "$RUNNER_TEMP/wr-iot-romfs.XXXXXX")"
trap 'find "$probe" -depth -delete' EXIT
cross="${compiler%gcc}"
if ! cmp -s "$trunk/linux-4.4.x/.config" "$results/ra2-no-host-module/kernel.config"; then
  diff -u "$trunk/linux-4.4.x/.config" "$results/ra2-no-host-module/kernel.config" \
    > "$results/isolated-romfs-kernel-config.diff" || test "$?" = 1
  echo '::error::Candidate kernel configuration differs from baseline; coherent kernel build required' >&2
  exit 1
fi
python3 -B tools/iot/stage-candidate-romfs.py "$trunk/romfs" "$results" \
  --manifest "$results/paired-image-inputs.json" --revision "$revision" \
  --kernel-config "$trunk/linux-4.4.x/.config" \
  --output "$probe/romfs" --report "$results/isolated-romfs-stage.json"
python3 -B tools/iot/check-classic-config-romfs.py
python3 -B tools/iot/stage-classic-config-romfs.py "$probe/romfs" \
  "$results/runtime-link/iot-edit-view-source.json" \
  --report "$results/isolated-classic-config.json"
# Use the real SDK destinations, rather than the earlier temporary RC probe path.
python3 tools/band-steering/verify-package-closure.py "$probe/romfs" "$probe/romfs" \
  --binary sbin/rc --binary usr/sbin/httpd --readelf "${cross}readelf" \
  --output "$results/isolated-romfs-dependency-closure.json"
# Inspect the exact staged module's modinfo using the selected toolchain.
module="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["module_destination"])' "$results/isolated-romfs-stage.json")"
"${cross}readelf" -p .modinfo "$probe/romfs/$module" > "$results/isolated-romfs-module-info.txt"
grep -Eq 'vermagic=4\.4\.198([[:space:]]|$)' "$results/isolated-romfs-module-info.txt"
"${cross}readelf" -sW "$probe/romfs/$module" > "$results/isolated-romfs-radio-symbols.txt"
python3 -B tools/iot/check-candidate-radio-features.py
python3 -B tools/iot/verify-candidate-radio-features.py "$trunk/linux-4.4.x/.config" \
  "$results/isolated-romfs-radio-symbols.txt" --report "$results/isolated-romfs-radio-features.json"

python3 - "$results" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);stage=json.loads((root/'isolated-romfs-stage.json').read_text())
closure=json.loads((root/'isolated-romfs-dependency-closure.json').read_text())
if not closure['dependency_closure_verified'] or closure['errors']:
 raise SystemExit('Actual-path dependency check failed')
for name in ['sbin/rc','usr/sbin/httpd']:
 if closure['elf_files']['candidate:'+name]['sha256']!=stage['replacement_sha256'][name]:
  raise SystemExit('Actual-path binary changed: '+name)
stage['dependency_closure_at_image_paths_verified']=True
stage['module_vermagic_checked']=True
(root/'isolated-romfs-stage.json').write_text(json.dumps(stage,indent=2)+'\n')
PY
printf '%s\n' 'PASS isolated real ROMFS staging and actual-path dependencies; no TRX or device acceptance'
# Use the pinned vendor image rules with isolated output directories. Do not run
# top-level romfs (which would reinstall/strip into the normal baseline tree).
mkdir "$probe/images"
cat > "$probe/image.mk" <<'MAKE'
.EXPORT_ALL_VARIABLES:
include $(ROOTDIR)/versions.inc
.DEFAULT_GOAL := isolated-image
.PHONY: isolated-image
isolated-image:
	$(MAKE) -C $(ROOTDIR)/vendors romfs.post image ROOTDIR=$(ROOTDIR) LINUXDIR=linux-4.4.x LINUX_CONFIG=$(ROOTDIR)/linux-4.4.x/.config PROJECT_CONFIG=$(ROOTDIR)/.config ARCH_CONFIG=$(ROOTDIR)/config.arch FIRMWARE_KERNEL_VER=4.4 CROSS_COMPILE=$(CROSS_COMPILE) ROMFSDIR=$(IOT_ROMFS) IMAGEDIR=$(IOT_IMAGES)
MAKE
sha256sum "$trunk/linux-4.4.x/vmlinux" "$trunk/linux-4.4.x/.config" \
  "$trunk/.config" "$trunk/config.arch" > "$results/isolated-image-baseline.sha256"
make -f "$probe/image.mk" ROOTDIR="$trunk" CROSS_COMPILE="$cross" \
  IOT_ROMFS="$probe/romfs" IOT_IMAGES="$probe/images" \
  2>&1 | tee "$results/isolated-image-build.log"
shopt -s nullglob
images=("$probe/images/"*.trx)
test "${#images[@]}" = 1
python3 overlay/padavan-4.4/scripts/verify-wr1200js-image.py "${images[0]}" \
  --report "$results/isolated-trx-board-gates.json"
python3 -B tools/iot/verify-isolated-trx.py "${images[0]}" "$probe/romfs" \
  --unsquashfs "$trunk/tools/mksquashfs_xz/unsquashfs" \
  --report "$results/isolated-trx-content.json"
python3 - "$results" "$probe/romfs" <<'PY'
import hashlib,json,sys
from pathlib import Path
root,romfs=map(Path,sys.argv[1:])
classic=json.loads((root/'isolated-classic-config.json').read_text())
content=json.loads((root/'isolated-trx-content.json').read_text())
if not content.get('isolated_trx_contents_verified') or not classic.get('classic_configuration_staged') or classic.get('classic_navigation_staged') is not True:
 raise SystemExit('Classic candidate TRX verification missing')
if set(classic['sha256'])!={'www/Advanced_IoT_Content.asp','www/classic-iot-config.js','www/state.js','www/classic-iot-navigation.js'}:
 raise SystemExit('Classic configuration/navigation payload incomplete')
for name,digest in classic['sha256'].items():
 path=romfs/name
 if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
  raise SystemExit('Classic payload changed before image verification: '+name)
classic['trx_verified']=True
classic['image_sha256']=content['image_sha256']
(root/'isolated-classic-config.json').write_text(json.dumps(classic,indent=2)+'\n')
PY
sha256sum -c "$results/isolated-image-baseline.sha256"
mkdir "$results/isolated-image"
cp "${images[0]}" "$results/isolated-image/WR1200JS-IoT-CANDIDATE-${revision:0:8}.trx"
sha256sum "$results/isolated-image/"*.trx > "$results/isolated-image.sha256"
python3 - "$results" "$revision" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);revision=sys.argv[2]
board=json.loads((root/'isolated-trx-board-gates.json').read_text())
content=json.loads((root/'isolated-trx-content.json').read_text())
stage=json.loads((root/'isolated-romfs-stage.json').read_text())
images=list((root/'isolated-image').glob('*.trx'))
if len(images)!=1:raise SystemExit('Require one retained candidate TRX')
digest=hashlib.file_digest(images[0].open('rb'),'sha256').hexdigest()
if board['sha256']!=digest or content['image_sha256']!=digest or not all(board['checks'].values()):
 raise SystemExit('Image reports do not describe the retained candidate')
if stage['source_revision']!=revision or not stage['baseline_unchanged'] or not stage['dependency_closure_at_image_paths_verified']:
 raise SystemExit('Staging proof does not match this source')
features=json.loads((root/'isolated-romfs-radio-features.json').read_text())
if not features['radio_feature_code_verified']:raise SystemExit('Radio feature code check failed')
report={'source_revision':revision,'candidate_image':images[0].name,'sha256':digest,
        'bytes':images[0].stat().st_size,'firmware_partition_bytes':16187392,
        'remaining_partition_bytes':16187392-images[0].stat().st_size,
        'isolated_image_build_verified':True,'board_structure_and_hwnat_policy_verified':True,'radio_feature_code_verified':True,
        'complete_romfs_extraction_verified':content['isolated_trx_contents_verified'],
        'dependency_closure_at_image_paths_verified':True,'production_promoted':False,
        'physical_runtime_verified':False}
(root/'isolated-image-verification.json').write_text(json.dumps(report,indent=2)+'\n')
PY
printf '%s\n' 'PASS isolated candidate TRX built/extracted; NOT runtime accepted or promoted to release'
