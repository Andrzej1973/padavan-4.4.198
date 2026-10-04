#!/usr/bin/env python3
"""Verify ZeroTier target binary, loader and recursive ROMFS dependencies."""
import argparse, hashlib, json, re, subprocess, os, struct
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,default=Path('zerotier-image-checks.json'))
a=p.parse_args()
romfs=(a.source/'trunk/romfs').resolve()
checks={}
errors=[]
visited={}
def target(path):
    path=Path(path)
    for _ in range(24):
        try:
            path.relative_to(romfs)
        except ValueError:
            raise ValueError('Path escapes ROMFS: '+str(path))
        if not path.is_symlink():
            if not path.is_file(): raise ValueError('Missing image file: '+str(path))
            return path
        link=Path(os.readlink(path))
        path=(romfs/str(link).lstrip('/')) if link.is_absolute() else path.parent/link
        path=Path(os.path.abspath(path))
    raise ValueError('Symlink loop in ROMFS')
def inspect(path):
    path=target(path)
    name=str(path.relative_to(romfs))
    if name in visited: return
    header=subprocess.check_output(['readelf','-h',str(path)],text=True)
    if not ('ELF32' in header and 'little endian' in header and re.search(r'Machine:.*MIPS',header)):
        raise ValueError('Non-target ELF: '+name)
    dynamic=subprocess.check_output(['readelf','-d',str(path)],text=True)
    dependencies=re.findall(r'\(NEEDED\).*\[([^\]]+)\]',dynamic)
    visited[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'needed':dependencies}
    for library in dependencies:
        choices=[romfs/'lib'/library,romfs/'usr/lib'/library]
        candidate=next((x for x in choices if x.exists() or x.is_symlink()),None)
        if candidate is None: raise ValueError('Unresolved '+library+' required by '+name)
        inspect(candidate)
def executable_digest(path):
    data=path.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x01': raise ValueError('Expected little-endian ELF32')
    phoff=struct.unpack_from('<I',data,28)[0]
    size,count=struct.unpack_from('<HH',data,42)
    segments=[]
    for index in range(count):
        kind,offset,vaddr,paddr,filesz,memsz,flags,align=struct.unpack_from('<IIIIIIII',data,phoff+index*size)
        if kind==1 and flags&1:
            start=max(offset,phoff+size*count) if offset==0 else offset
            if offset+filesz>len(data): raise ValueError('Truncated executable load segment')
            segments.append(hashlib.sha256(data[start:offset+filesz]).hexdigest())
    if not segments: raise ValueError('No executable load segment')
    return segments
try:
    source=a.source/'trunk/user/zerotier/ZeroTierOne-1.16.2'
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if revision!='fe29cd88886e4f58547ba7f740b2d73eb49ab222': raise ValueError('Wrong ZeroTier source revision')
    version=(source/'version.h').read_text()
    for suffix,value in [('MAJOR',1),('MINOR',16),('REVISION',2)]:
        if not re.search(r'^#define ZEROTIER_ONE_VERSION_'+suffix+r'\s+'+str(value)+r'\s*$',version,re.M):
            raise ValueError('Unexpected source version')
    binary=romfs/'usr/bin/zerotier-one'
    inspect(binary)
    if executable_digest(source/'zerotier-one')!=executable_digest(target(binary)):
        raise ValueError('ROMFS executable differs from source-built ZeroTier code')
    checks['source_revision_version_and_image_code']=True
    program_headers=subprocess.check_output(['readelf','-l',str(binary)],text=True)
    interpreter=re.search(r'Requesting program interpreter:\s*([^\]]+)\]',program_headers)
    if not interpreter: raise ValueError('No target ELF interpreter')
    inspect(romfs/interpreter.group(1).strip().lstrip('/'))
    for name in ['zerotier-cli','zerotier-idtool']:
        if target(romfs/'usr/bin'/name)!=target(binary): raise ValueError('Broken '+name+' symlink')
    checks['target_binary_and_dependency_closure']=True
    if not (romfs/'usr/bin/zerotier.sh').is_file(): raise ValueError('Missing lifecycle helper')
    checks['lifecycle_helper']=True
except (ValueError,OSError,subprocess.CalledProcessError) as error:
    errors.append(str(error))
result={'package':'zerotier','candidate_version':'1.16.2','checks':checks,'elf_files':visited,'errors':errors,'runtime_verified':False}
a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(1 if errors else 0)

