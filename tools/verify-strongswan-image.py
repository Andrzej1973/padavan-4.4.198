"""Check packaged IPsec files; library availability is not loader/runtime proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('trunk', type=Path)
p.add_argument('report', type=Path)
a = p.parse_args()
root = (a.trunk / 'romfs').resolve()
spec = importlib.util.spec_from_file_location('image_paths', Path(__file__).parent / 'band-steering/verify-package-closure.py')
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)
checks, details = {}, {'files': {}, 'dynamic_search_paths': {}, 'missing_libraries': []}
def file(name):
    return paths.resolve_image(root, name.lstrip('/'))
def elf(path):
    data=path.read_bytes()[:20]
    return len(data)==20 and data[:6]==b'\x7fELF\x01\x01' and int.from_bytes(data[18:20],'little')==8
try:
    checks['selector']='CONFIG_FIRMWARE_INCLUDE_SSWAN=y' in (a.trunk/'.config').read_text().splitlines()
    for name in ('usr/sbin/ipsec','usr/libexec/ipsec/_updown'):
        path=file(name)
        checks[name]=bool(path.stat().st_mode&0o111) and path.read_bytes().startswith(b'#!')
        checks[name+'_syntax']=subprocess.run(['sh','-n',str(path)],capture_output=True).returncode==0
    queue=[file('usr/libexec/ipsec/'+name) for name in ('charon','starter','stroke')]
    seen=set()
    while queue:
        path=queue.pop()
        if path in seen:continue
        seen.add(path)
        relative=path.relative_to(root).as_posix()
        if not elf(path):raise ValueError('Expected ELF32 little-endian MIPS: '+relative)
        if not path.stat().st_mode&0o111 and relative.startswith('usr/libexec/'):
            raise ValueError('Nonexecutable IPsec program: '+relative)
        details['files'][relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        dynamic=subprocess.check_output(['readelf','-d',str(path)],text=True)
        details['dynamic_search_paths'][relative]=re.findall(r'\((?:RPATH|RUNPATH)\).*\[([^\]]+)\]',dynamic)
        for name in re.findall(r'\(NEEDED\).*\[([^\]]+)\]',dynamic):
            if '/' in name or name in ('.','..'):raise ValueError('Invalid library name')
            found=None
            for directory in ('lib','usr/lib','usr/lib/ipsec'):
                try:found=file(directory+'/'+name)
                except ValueError as error:
                    if not str(error).startswith('Missing image file:'):raise
                if found is not None:break
            if found is None:details['missing_libraries'].append(name)
            else:queue.append(found)
        headers=subprocess.check_output(['readelf','-l',str(path)],text=True)
        for loader in re.findall(r'Requesting program interpreter:\s*([^\]]+)\]',headers):
            queue.append(file(loader.strip()))
    checks['dependency_files_present']=not details['missing_libraries']
    checks['mips_files_inspected']=len(seen)>=3
except (OSError,ValueError,subprocess.CalledProcessError) as error:
    checks['inspection_completed']=False;details['error']=str(error)
a.report.write_text(json.dumps({'scope':'IPsec packaging, architecture and dependency-file availability; loader search behavior, service lifecycle, credentials, firewall and VPN runtime unverified','checks':checks,'details':details},indent=2)+'\n')
if not all(checks.values()):raise SystemExit('StrongSwan image checks failed: '+', '.join(k for k,v in checks.items() if not v))
print('PASS StrongSwan image files and dependency availability; service/runtime remain unverified')
