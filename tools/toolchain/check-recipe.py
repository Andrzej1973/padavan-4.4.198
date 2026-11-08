#!/usr/bin/env python3
"""Lightweight negative checks for source recipe and target ABI acceptance."""
import importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parent.parent

def load(name):
 spec=importlib.util.spec_from_file_location(name,here/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
config=load('check-config');verifier=load('verify')
profile=(root/'toolchains/wr1200js/crosstool.config').read_text()
# GCC_VERSION is a generated Kconfig default, not a user-provided mirror profile.
normalized=profile+'\nCT_GCC_VERSION="10.5.0"\n'
config.check(normalized)
for old,new in [('CT_ARCH_LE=y','CT_ARCH_LE=n'),('CT_GCC_VERSION="10.5.0"','CT_GCC_VERSION="7.5.0"'),('CT_VERIFY_DOWNLOAD_DIGEST=y','CT_VERIFY_DOWNLOAD_DIGEST=n'),('CT_INSTALL_LICENSES=y','CT_INSTALL_LICENSES=n'),('source/trunk/linux-4.4.x','source/trunk/linux-3.4.x')]:
 try:config.check(normalized.replace(old,new))
 except ValueError:pass
 else:raise AssertionError('Accepted drift '+old)
try:config.check(normalized+'CT_ARCH_LE=y\n')
except ValueError:pass
else:raise AssertionError('Accepted duplicate setting')
data=bytearray(52);data[:6]=b'\x7fELF\x01\x01';data[18:20]=(8).to_bytes(2,'little');data[36:40]=(0x70001000).to_bytes(4,'little')
verifier.elf(data)
for offset,value in [(4,2),(5,2),(18,62),(39,0x50),(37,0)]:
 bad=bytearray(data);bad[offset]=value
 try:verifier.elf(bad)
 except ValueError:pass
 else:raise AssertionError('Accepted wrong ELF ABI')
lock=json.loads((root/'toolchains/wr1200js/sources.json').read_text())
assert lock['expected']=={'target':'mipsel-linux-uclibc','gcc':'10.5.0','libc':'1.0.48','linux_headers':'4.4.198'}
for key in ['ctng','libc']:assert len(lock[key]['sha256'])==64
subprocess.run(['bash','-n',str(here/'build.sh')],check=True)
workflow=(root/'.github/workflows/build-owned-toolchain.yml').read_text()
assert 'queue: max' in workflow and 'cancel-in-progress: false' in workflow
assert '--prerelease --latest=false' in workflow
assert 'timeout-minutes: 240' in workflow
print('PASS source recipe: profile drift/duplicate, bad ELF/endian/architecture/O32 rejection, shell syntax, isolated queue and candidate publication')
