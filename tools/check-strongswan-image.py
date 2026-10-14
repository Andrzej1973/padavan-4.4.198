"""Synthetic negative tests of the actual StrongSwan image checker."""
from pathlib import Path
import contextlib
import io
import json
import os
import stat
import runpy
import shutil
import subprocess
import sys
from unittest.mock import patch
import uuid

directory=Path.cwd()/('sswan-image-check-'+uuid.uuid4().hex);directory.mkdir()
root=directory/'romfs';tool=Path(__file__).with_name('verify-strongswan-image.py')
elf=b'\x7fELF\x01\x01'+b'\0'*12+b'\x08\x00'+b'\0'*32
def write(name,data):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o755);return path
try:
    (directory/'.config').write_text('CONFIG_FIRMWARE_INCLUDE_SSWAN=y\n')
    for name in ('usr/sbin/ipsec','usr/libexec/ipsec/_updown'):write(name,b'#!/bin/sh\nexit 0\n')
    for name in ('charon','starter','stroke'):write('usr/libexec/ipsec/'+name,elf)
    library=write('usr/lib/ipsec/libstrongswan.so.0',elf)
    loader=write('lib/ld-uClibc.so.0',elf)
    bad_loader=False
    def readelf(args,**kwargs):
        executable='/usr/libexec/ipsec/' in Path(args[-1]).as_posix()
        if args[1]=='-d':return '(NEEDED) Shared library: [libstrongswan.so.0]\n' if executable else ''
        assert args[1]=='-l'
        return '[Requesting program interpreter: /lib/ld-uClibc.so.0]\n' if executable and not bad_loader else ''
    def check(ok):
        report=directory/'report.json';status=0
        native_stat=Path.stat
        def posix_mode(path,*args,**kwargs):
            observed=native_stat(path,*args,**kwargs)
            if path.is_relative_to(root) and stat.S_ISREG(observed.st_mode):
                fields=list(observed);fields[0]|=0o111;return os.stat_result(fields)
            return observed
        mode_patch=patch.object(Path,'stat',posix_mode) if os.name=='nt' else contextlib.nullcontext()
        with mode_patch,patch.object(sys,'argv',[str(tool),str(directory),str(report)]),patch.object(subprocess,'check_output',side_effect=readelf),patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0)),contextlib.redirect_stdout(io.StringIO()):
            try:runpy.run_path(str(tool),run_name='__main__')
            except SystemExit as error:status=error.code
        assert (status==0)==ok,(status,report.read_text())
        return json.loads(report.read_text())
    check(True)
    library.unlink();assert check(False)['details']['missing_libraries'];library.write_bytes(elf)
    loader.unlink();check(False);loader.write_bytes(elf)
    program=root/'usr/libexec/ipsec/charon';program.write_bytes(b'wrong architecture');check(False);program.write_bytes(elf)
    bad_loader=True;check(False);bad_loader=False
    (directory/'.config').write_text('CONFIG_FIRMWARE_INCLUDE_SSWAN=n\n');check(False)
finally:
    assert directory.resolve().parent==Path.cwd().resolve()
    shutil.rmtree(directory)
print('PASS StrongSwan image gate rejects missing dependency/loader, invalid architecture, absent interpreter and disabled selector; synthetic readelf fixture only')
