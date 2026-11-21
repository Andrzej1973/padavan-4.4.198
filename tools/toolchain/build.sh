#!/usr/bin/env bash
# Source-only candidate builder. Heavy compilation belongs on GitHub Actions.
set -euo pipefail
if [ "${GITHUB_ACTIONS:-}" != true ]; then echo "Full toolchain builds run only in GitHub Actions" >&2; exit 1; fi
repo=$(git rev-parse --show-toplevel)
work=$(realpath -m "$1")
results=$(realpath -m "$2")
test ! -e "$work"
case "$results/" in "$work/"*) echo 'Results must survive scratch cleanup' >&2; exit 1;; esac
cd "$repo"
mkdir -p "$work" "$results"
cp "$repo/toolchains/wr1200js/sources.json" "$results/sources.json"
cp "$repo/toolchains/wr1200js/crosstool.config" "$results/requested.config"
# Every removed path is the fresh phase directory created above; cache lives outside it.
cleanup() { du -sh "$work"; rm -rf -- "$work"; }
trap cleanup EXIT
python3 - "$repo/toolchains/wr1200js/sources.json" "$work" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
lock=json.loads(Path(sys.argv[1]).read_text());work=Path(sys.argv[2])
for key,name in [('ctng','ctng.tar.xz'),('libc','uClibc-ng-1.0.48.tar.xz')]:
 p=work/name
 subprocess.run(['curl','--fail','--location','--retry','3','--connect-timeout','20','--max-time','300','-H','Accept: application/octet-stream','-o',str(p),lock[key]['url']],check=True)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=lock[key]['sha256']:raise SystemExit('Source digest mismatch: '+key)
PY
revision=$(python3 -c 'import json;print(json.load(open("toolchains/wr1200js/sources.json"))["padavan"]["revision"])')
mkdir "$work/source"
git -C "$work/source" init
git -C "$work/source" remote add origin https://github.com/vipshmily/padavan-4.4.git
git -C "$work/source" sparse-checkout init --no-cone
git -C "$work/source" sparse-checkout set '/trunk/linux-4.4.x/' '/trunk/configs/boards/uclibc-mipsel.config'
python3 "$repo/tools/retry-source-command.py" --timeout 900 git -C "$work/source" fetch --depth=1 --filter=blob:none origin "$revision"
git -C "$work/source" checkout --detach FETCH_HEAD
test "$(git -C "$work/source" rev-parse HEAD)" = "$revision"
tar -xJf "$work/ctng.tar.xz" -C "$work"
ctng="$work/crosstool-ng-1.26.0"
cp "$repo/toolchains/wr1200js/crosstool.config" "$ctng/.config"
mkdir -p "$TOOLCHAIN_SOURCE_CACHE"
ln -s "$TOOLCHAIN_SOURCE_CACHE" "$ctng/dl"
cd "$ctng"
./configure --enable-local 2>&1 | tee "$results/configure.log"
make -j2 2>&1 | tee "$results/generator.log"
./ct-ng olddefconfig 2>&1 | tee "$results/olddefconfig.log"
cp .config "$results/effective.config"
python3 "$repo/tools/toolchain/check-config.py" .config
./ct-ng build 2>&1 | tee "$results/build.log"
# Move the finished tree before smoke testing to exercise relocatability.
mv out "$work/relocated"
python3 "$repo/tools/toolchain/verify.py" "$work/relocated" "$results"
# Keep exact inputs, fetched package archives and Linux sources with the binary.
# Exclude Git metadata and build intermediates; never archive credentials/cache state.
cp "$repo/toolchains/wr1200js/crosstool.config" "$work/profile.config"
cp "$repo/toolchains/wr1200js/sources.json" "$work/sources.json"
cp "$results/effective.config" "$work/effective.config"
cp -a "$repo/tools/toolchain" "$work/recipe"
tar --sort=name --mtime='UTC 2026-11-08' --owner=0 --group=0 --numeric-owner \
  -cJf "$results/mipsel-linux-uclibc-source-candidate.tar.xz" -C "$work/relocated" .
tar --sort=name --mtime='UTC 2026-11-08' --owner=0 --group=0 --numeric-owner \
  --exclude='.git' --exclude='__pycache__' -cJf "$results/toolchain-build-sources.tar.xz" -C "$work" \
  ctng.tar.xz uClibc-ng-1.0.48.tar.xz profile.config effective.config sources.json recipe source/trunk
# Package tarballs are already compressed; archive only the tarballs, not any cache metadata.
find "$TOOLCHAIN_SOURCE_CACHE" -maxdepth 1 -type f -name '*.tar.*' -printf '%f\0' | sort -z > "$work/tarballs.list"
tar -cJf "$results/toolchain-package-sources.tar.xz" -C "$TOOLCHAIN_SOURCE_CACHE" --null -T "$work/tarballs.list"
cd "$results"
sha256sum ./*.tar.xz > SHA256SUMS
python3 - "$repo" "$results" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
repo=Path(sys.argv[1]);r=Path(sys.argv[2]);out=json.loads((r/'verification.json').read_text())
out['project_revision']=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
out['sources']=json.loads((r/'sources.json').read_text())
out['profile_sha256']=hashlib.sha256((r/'effective.config').read_bytes()).hexdigest()
out['archives']={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in r.glob('*.tar.xz')}
out['production_promoted']=False;out['device_runtime_verified']=False
(r/'result.json').write_text(json.dumps(out,indent=2)+'\n')
PY
