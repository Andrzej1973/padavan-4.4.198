#!/usr/bin/env python3
"""Mocked restore orchestration; never bind a real USB device."""
from pathlib import Path
import os
import subprocess
import tempfile
here=Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='usbip-restore-') as tmp:
    root=Path(tmp);devices=root/'devices';devices.mkdir();events=root/'events';table=root/'table'
    for bus,serial in [('1-1','unit1'),('1-2','unit2')]:
        d=devices/bus;d.mkdir()
        for key,value in [('idVendor','1234'),('idProduct','abcd'),('serial',serial)]:
            (d/key).write_text(value+'\n')
    reader=root/'reader';reader.write_text('#!/bin/sh\ncat "$TABLE"\nexit "${READER_FAIL:-0}"\n');reader.chmod(0o700)
    source=(here/'restore.sh').read_text().replace('/sys/bus/usb/devices',str(devices)).replace('/usr/libexec/wr-usbip/export-table',str(reader))
    script=root/'run.sh';script.write_text('''set -eu
nvram(){ case "$2" in usbip_enable) echo "${ENABLE:-1}";; usbip_restore) echo "${RESTORE:-1}";; esac; }
snapshot(){ owned_pid=${OWNED-234}; }
wr_usbip_device_check(){ test "$1" != "${BLOCK_BUS:-none}" || return 1; wr_usbip_device="$DEVICES/$1"; test -d "$wr_usbip_device"; }
'''+(here/'device-action.sh').read_text()+'''
wr_usbip_device_action(){ printf '%s %s\n' "$1" "$2" >> "$EVENTS"; }
'''+source+'\nif wr_usbip_restore_exports; then exit 0; else exit 1; fi\n')
    rows='1-1\t1234\tabcd\t'+b'unit1'.hex()+'\n1-2\t1234\tabcd\t'+b'unit2'.hex()+'\n'
    env=dict(os.environ,DEVICES=str(devices),EVENTS=str(events),TABLE=str(table))
    def run(data=rows,**extra):
        table.write_text(data);events.write_text('')
        result=subprocess.run(['sh',str(script)],env=dict(env,**extra),capture_output=True,text=True)
        return result.returncode,events.read_text()
    assert run(RESTORE='0')==(0,'')
    assert run(ENABLE='0')==(0,'')
    assert run('')==(0,'')
    assert run(READER_FAIL='2')==(1,'')
    assert run(OWNED='')==(1,'')
    assert run(BLOCK_BUS='1-2')==(1,'') # all-rule preflight before first bind
    assert run()==(0,'bind 1-1\nbind 1-2\n')
    (devices/'1-2/serial').write_text('unit1\n');assert run()==(1,'')
    (devices/'1-2/serial').unlink();assert run()==(1,'')
print('PASS USBIP restore: disabled/empty, reader failure, daemon, batch preflight, serial uniqueness and guarded dispatch')
