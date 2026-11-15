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
# Use the real SDK destinations, rather than the earlier temporary RC probe path.
python3 tools/band-steering/verify-package-closure.py "$probe/romfs" "$probe/romfs" \
  --binary sbin/rc --binary usr/sbin/httpd --readelf "${cross}readelf" \
  --output "$results/isolated-romfs-dependency-closure.json"
# Inspect the exact staged module's modinfo using the selected toolchain.
module="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["module_destination"])' "$results/isolated-romfs-stage.json")"
"${cross}readelf" -p .modinfo "$probe/romfs/$module" > "$results/isolated-romfs-module-info.txt"
grep -Eq 'vermagic=4\.4\.198([[:space:]]|$)' "$results/isolated-romfs-module-info.txt"
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
python3 -B tools/iot/verify-isolated-trx.py "${images[0]}" "$probe/romfs" \
  --unsquashfs "$trunk/tools/mksquashfs_xz/unsquashfs" \
  --report "$results/isolated-trx-content.json"
sha256sum -c "$results/isolated-image-baseline.sha256"
mkdir "$results/isolated-image"
cp "${images[0]}" "$results/isolated-image/WR1200JS-IoT-CANDIDATE-${revision:0:8}.trx"
sha256sum "$results/isolated-image/"*.trx > "$results/isolated-image.sha256"
printf '%s\n' 'PASS isolated candidate TRX built/extracted; NOT runtime accepted or promoted to release'
