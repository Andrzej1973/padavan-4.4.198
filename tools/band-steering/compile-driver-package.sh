#!/bin/bash
# Compile/stage only: use the actual isolated, already-built driver tree.
# Nothing is installed into the normal firmware ROMFS and no service is started.
set -euo pipefail
root="$(realpath "$1")"
probe="$2"
compiler="$(realpath "$3")"
test -x "$compiler"
test ! -e "$probe"
for radio in mt76x2 mt76x3; do
  test -s "$root/trunk/linux-4.4.x/drivers/net/wireless/mediatek/${radio}_ap/${radio}_ap.ko"
done
mkdir -p "$probe"
probe="$(realpath "$probe")"
python3 tools/band-steering/prepare-abi-probe.py "$root" --output "$probe/abi"
for radio in mt76x2 mt76x3; do
  "$compiler" -std=gnu11 -mips32r2 -mabi=32 -msoft-float -O2 -c \
    "$probe/abi/$radio-abi.c" -o "$probe/abi/$radio-abi.o"
done
python3 tools/band-steering/read-abi-probe.py "$probe/abi"
make -f tools/band-steering/package/Makefile romfs \
  SOURCE_DIR="$PWD/tools/band-steering" LAYOUT_DIR="$probe/abi" \
  BUILD_DIR="$probe/build" INSTALLDIR="$probe/romfs" CC="$compiler" \
  CFLAGS="-O2 -mips32r2 -mabi=32 -msoft-float" \
  2>&1 | tee "$probe/build.log"
cross="${compiler%gcc}"
for binary in wr-band-steering wr-band-steering-ctl; do
  file="$probe/romfs/usr/sbin/$binary"
  test -x "$file"
  "${cross}readelf" -h -l -d "$file" > "$probe/$binary-elf.txt"
  grep -q 'Machine:.*MIPS' "$probe/$binary-elf.txt"
done
python3 - "$probe" "$root" <<'PY'
import hashlib,json,sys
from pathlib import Path
p,root=map(Path,sys.argv[1:])
files=sorted(f.relative_to(p/'romfs').as_posix() for f in (p/'romfs').rglob('*') if f.is_file())
assert files==['usr/sbin/wr-band-steering','usr/sbin/wr-band-steering-ctl'],files
def record(f):
    data=f.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
drivers={radio:record(root/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/
    (radio+'_ap')/(radio+'_ap.ko')) for radio in ('mt76x2','mt76x3')}
report={'runtime_verified':False,'production_installed':False,'startup_hooks':False,
    'drivers':drivers,'binaries':{f:record(p/'romfs'/f) for f in files},
    'layout':record(p/'abi/protocol-layout.h')}
(p/'package-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY
