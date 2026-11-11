#!/usr/bin/env python3
"""Compile isolated CGI candidate with the built firmware's real make environment.
Never runs romfs/install or changes the production HTTP source/binary.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.source.resolve(strict=True)
output=args.output.resolve()
output.mkdir(parents=True,exist_ok=True)
httpd=root/'trunk/user/httpd'
production=root/'trunk/romfs/usr/sbin/httpd'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before={'source':digest(httpd/'web_ex.c'),'server_source':digest(httpd/'httpd.c'),'cgi_source':digest(httpd/'cgi.c'),'image_binary':digest(production)}
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip()
report={'scope':'Isolated complete target HTTP candidate compile/link, not installation or runtime',
        'repository_revision':revision,'production_before':before,'target_compiled':False,'production_installed':False,'runtime_verified':False}
try:
    with tempfile.TemporaryDirectory(prefix='wr-modern-http-source-') as scratch:
        prepared=Path(scratch)
        copied=prepared/'trunk/user/httpd'
        shutil.copytree(httpd,copied,ignore=shutil.ignore_patterns('*.o','*.d','httpd','*~'))
        subprocess.run(['python3',str(Path(__file__).parent/'prepare-password-candidate.py'),str(prepared)],check=True)
        subprocess.run(['python3',str(Path(__file__).parent/'prepare-guest-candidate.py'),str(prepared)],check=True)
        subprocess.run(['python3',str(Path(__file__).parent/'prepare-guest-transport.py'),str(prepared)],check=True)
        subprocess.run(['python3',str(Path(__file__).parent/'prepare-modern-body.py'),str(prepared)],check=True)
        subprocess.run(['python3',str(Path(__file__).parent/'prepare-guest-json.py'),str(prepared)],check=True)
        report['candidate_web_ex_sha256']=digest(copied/'web_ex.c')
        # A sibling package preserves ../../ROOTDIR and existing shared libraries.
        with tempfile.TemporaryDirectory(prefix='wr-modern-http-build-',dir=root/'trunk/user') as target:
            target=Path(target)
            shutil.copytree(copied,target,dirs_exist_ok=True)
            command=['make','-C',str(root/'trunk'),'user/'+target.name+'_only',
                     'TOOLCHAIN=mipsel-linux-uclibc','CONFIG_CCACHE=y']
            report['command']=command
            log=output/'compile.log'
            with log.open('w') as stream:
                result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
            report['compile_exit_code']=result.returncode
            if result.returncode:
                print('\n'.join(log.read_text(errors='replace').splitlines()[-80:])[-16000:])
                raise RuntimeError('Modern isolated HTTP candidate compile failed; see compile.log')
            binary=target/'httpd'
            data=binary.read_bytes()
            if data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:
                raise RuntimeError('Candidate is not ELF32 little-endian MIPS')
            guards=(b'Invalid Modern credential request. No settings were saved.',
                    b'Invalid Modern Guest request. No settings were saved.',
                    b'Invalid Modern body framing.', b'Invalid Modern body.',
                    b'wr_modern_guest_apply.json', b'reload_required', b'requested_unverified')
            if any(marker not in data for marker in guards):
                raise RuntimeError('Candidate credential/Guest/body guard missing from linked binary')
            dynamic=subprocess.check_output(['readelf','-d',str(binary)],text=True)
            (output/'readelf-dynamic.txt').write_text(dynamic)
            report.update(target_compiled=True,binary_bytes=len(data),binary_sha256=digest(binary),elf='ELF32 little-endian MIPS',
                          candidate_headers_sha256={name:digest(copied/'wr-shared-wifi'/name) for name in ('password-intent.h','password-request.h','guest-schedule.h','guest-request.h','guest-adapter.h','guest-transport.h','modern-form.h','modern-body.h')})
            shutil.copyfile(binary,output/'httpd-candidate')
finally:
    report['production_after']={'source':digest(httpd/'web_ex.c'),'server_source':digest(httpd/'httpd.c'),'cgi_source':digest(httpd/'cgi.c'),'image_binary':digest(production)}
    report['production_unchanged']=report['production_after']==before
    report['scratch_removed']=True
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['production_unchanged']:
        raise RuntimeError('Production source/image changed during isolated candidate check')
print('PASS isolated complete MIPS HTTP candidate; production unchanged; scratch removed; runtime unverified')
