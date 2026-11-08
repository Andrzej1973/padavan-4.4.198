#!/usr/bin/env python3
"""Capture built image/config/ELF evidence, not device acceptance."""
import hashlib,json,os,subprocess,sys,re
from pathlib import Path
root=Path(sys.argv[1]);romfs=root/'trunk/romfs'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
import importlib.util
spec=importlib.util.spec_from_file_location('tool_paths',Path(__file__).with_name('tool-paths.py'))
tool_paths=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool_paths)
compiler,readelf=tool_paths.select(root/'toolchain/toolchain-mipsel')
def command(*args):return subprocess.check_output([str(x) for x in args],text=True)
files={}
for p in sorted(romfs.rglob('*')):
 if not p.is_file() or p.is_symlink():continue
 with p.open('rb') as stream:magic=stream.read(4)
 if magic==b'\x7fELF':
  with p.open('rb') as stream:header=stream.read(52)
  details=command(readelf,'-h','-A','-d','-l',p)
  files[str(p.relative_to(romfs))]={'sha256':digest(p),'bytes':p.stat().st_size,'elf':details,'abi':{'class':header[4],'endian':header[5],'machine':int.from_bytes(header[18:20],'little'),'arch_abi_flags':int.from_bytes(header[36:40],'little') & 0xf000f000,'needed':sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]',details)),'interpreter':re.findall(r'Requesting program interpreter: ([^\]]+)',details)}}
images={p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in (root/'trunk/images').glob('*.trx')}
if not images or not files:raise SystemExit('Missing image/ELF evidence')
configs={n:{'sha256':digest(Path(n)),'text':Path(n).read_text()} for n in ['firmware-effective.config','kernel-effective.config']}
r={'source_sha':command('git','rev-parse','HEAD').strip(),'variant':os.environ['TOOLCHAIN_VARIANT'],'compiler':command(compiler,'--version'),'target':command(compiler,'-dumpmachine').strip(),'configs':configs,'images':images,'elf_files':files,'runtime_verified':False,'production_promoted':False}
Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n')
