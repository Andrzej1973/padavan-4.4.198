#!/usr/bin/env python3
"""Cross-compile/link after relocation and execute candidate ABI probes in QEMU."""
import hashlib,json,subprocess,sys
from pathlib import Path

def elf(data):
 if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:raise ValueError('Expected ELF32 little-endian MIPS')
 flags=int.from_bytes(data[36:40],'little')
 if flags&0xf0000000!=0x70000000 or flags&0xf000!=0x1000:raise ValueError('Expected MIPS32r2 O32 ABI')
 return flags

def run(args,**kw):return subprocess.check_output([str(x) for x in args],text=True,**kw).strip()

def verify(prefix,results):
 gcc=prefix/'bin/mipsel-linux-uclibc-gcc';gxx=prefix/'bin/mipsel-linux-uclibc-g++'
 if run([gcc,'-dumpmachine'])!='mipsel-linux-uclibc':raise ValueError('Wrong target triplet')
 if run([gcc,'-dumpfullversion'])!='10.5.0':raise ValueError('Wrong GCC version')
 sysroot=Path(run([gcc,'-print-sysroot'])).resolve()
 if not sysroot.is_relative_to(prefix.resolve()):raise ValueError('Sysroot did not relocate with toolchain')
 macros=run([gcc,'-dM','-E','-x','c','-'],input='#include <features.h>\n#include <linux/version.h>\n')
 values=dict(line.split(maxsplit=2)[1:] for line in macros.splitlines() if line.startswith('#define ') and len(line.split(maxsplit=2))==3)
 for name,value in {'__UCLIBC_MAJOR__':'1','__UCLIBC_MINOR__':'0','__UCLIBC_SUBLEVEL__':'48','LINUX_VERSION_CODE':str((4<<16)+(4<<8)+198),'__MIPSEL__':'1'}.items():
  if values.get(name)!=value:raise ValueError('Wrong libc/header/endianness: '+name+'='+str(values.get(name)))
 results.mkdir(parents=True,exist_ok=True)
 c=results/'probe.c';cpp=results/'probe.cpp'
 c.write_text('''#include <pthread.h>
#include <math.h>
#include <stdio.h>
static __thread int value=7;
static void *worker(void *arg){(void)arg;value=23;return (void *)(long)value;}
int main(void){pthread_t thread;void *out=0;volatile double x=0.5;
if(pthread_create(&thread,0,worker,0)||pthread_join(thread,&out)||out!=(void *)23||value!=7||sin(x)<0.4)return 1;
puts("PASS MIPS C pthread TLS math");return 0;}
''')
 cpp.write_text('''#include <string>
#include <stdexcept>
#include <iostream>
int main(){try {throw std::runtime_error(std::string("probe"));}
catch(const std::exception &e){if(std::string(e.what())!="probe")return 1;}
std::cout<<"PASS MIPS C++ exceptions"<<std::endl;return 0;}
''')
 probes={}
 for name,compiler,source,extra in [('c',gcc,c,['-pthread','-lm']),('cpp',gxx,cpp,[])]:
  exe=results/('probe-'+name)
  subprocess.run([str(compiler),'-mips32r2','-mtune=1004kc','-O2',str(source),*extra,'-o',str(exe)],check=True)
  data=exe.read_bytes();flags=elf(data)
  qemu=['qemu-mipsel','-L',sysroot]
  if name=='cpp':
   lib=Path(run([gxx,'-print-file-name=libstdc++.so'])).resolve()
   if not lib.is_file() or not lib.is_relative_to(prefix.resolve()):raise ValueError('C++ runtime did not relocate')
   qemu+=['-E','LD_LIBRARY_PATH='+str(lib.parent)]
  output=run([*qemu,exe])
  if not output.startswith('PASS MIPS '):raise ValueError('Probe failed: '+name)
  probes[name]={'sha256':hashlib.sha256(data).hexdigest(),'elf_flags':hex(flags),'qemu_output':output}
 licenses=prefix/'share/licenses'
 if not licenses.is_dir() or not any(p.is_file() for p in licenses.rglob('*')):raise ValueError('Missing installed license inventory')
 result={'compiler_version':run([gcc,'--version']),'target':'mipsel-linux-uclibc','gcc':'10.5.0','libc':'1.0.48','linux_headers':'4.4.198','relocation_tested':True,'qemu_user_verified':True,'device_runtime_verified':False,'production_promoted':False,'probes':probes}
 (results/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS relocated MIPS O32 C/C++ linkage, QEMU pthread/TLS/math/exceptions and exact libc/kernel headers')

if __name__=='__main__':verify(Path(sys.argv[1]),Path(sys.argv[2]))
