#!/usr/bin/env python3
"""Execute controller device actions with mocked preflight and USB/IP binary."""
from pathlib import Path
import os
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='wr-usbip-action-') as directory:
    root=Path(directory)
    device=root/'device';device.mkdir()
    (device/'idVendor').write_text('1234\n')
    (device/'idProduct').write_text('abcd\n')
    (device/'usbip_status').write_text('1\n')
    (device/'serial').write_text('unit-test-only\n')
    events=root/'events'
    binary=root/'usbip'
    binary.write_text('''#!/bin/sh
echo "$*" >> "$EVENTS"
test ! -e /proc/self/fd/9 || exit 3
test "${FAIL:-0}" = 0 || exit 1
case "$1" in
 bind) ln -s /sys/bus/usb/drivers/usbip-host "$DEVICE/driver";;
 unbind) rm "$DEVICE/driver";;
 *) exit 2;;
esac
test "${REPLACE_SERIAL:-0}" = 0 || printf 'changed\n' > "$DEVICE/serial"
''')
    binary.chmod(0o755)
    source=Path(__file__).with_name('device-action.sh').read_text().replace('/sbin/usbip',str(binary))
    script=root/'run.sh'
    script.write_text('''set -eu
snapshot() { owned_pid=${OWNED-234}; }
wr_usbip_device_check() { wr_usbip_device=$DEVICE; test "${CHECK:-1}" = 1; }
'''+source+'\nexec 9>"$DEVICE/lock"\nif wr_usbip_device_action "$@"; then exit 0; else exit 1; fi\n')
    env=dict(os.environ,DEVICE=str(device),EVENTS=str(events))
    def run(action,vendor='1234',product='abcd',serial=None,**extra):
        events.write_text('')
        args=['sh',str(script),action,'1-1',vendor,product]
        if serial is not None:args.append(serial)
        result=subprocess.run(args,env=dict(env,**extra),capture_output=True,text=True)
        return result.returncode,events.read_text()
    assert run('bind',vendor='ffff')[0]!=0 and events.read_text()==''
    assert run('bind',vendor='1234;id')[0]!=0 and events.read_text()==''
    assert run('bind',OWNED='')[0]!=0 and events.read_text()==''
    assert run('bind',CHECK='0')[0]!=0 and events.read_text()==''
    assert run('bind',FAIL='1')[0]!=0
    rc,trace=run('bind');assert rc==0 and trace=='bind -b 1-1\n'
    rc,trace=run('bind');assert rc==0 and trace==''
    (device/'usbip_status').write_text('2\n')
    assert run('unbind')[0]!=0 and events.read_text()==''
    (device/'usbip_status').write_text('1\n')
    rc,trace=run('unbind');assert rc==0 and trace=='unbind -b 1-1\n'
    identity='unit-test-only'.encode().hex()
    for invalid in ['', 'f', '00', 'AB', 'x'*514]:
        assert run('bind',serial=invalid)[0]!=0 and events.read_text()==''
    rc,trace=run('bind',serial=identity);assert rc==0 and trace=='bind -b 1-1\n'
    rc,trace=run('unbind',serial=identity);assert rc==0 and trace=='unbind -b 1-1\n'
    assert run('bind',serial=identity,REPLACE_SERIAL='1')[0]!=0
    assert events.read_text()=='bind -b 1-1\n' # changed after action: report unconfirmed
    assert run('unbind')[0]==0
    (device/'serial').write_text('x'*300+'\n')
    assert run('bind',serial=identity)[0]!=0 and events.read_text()==''
    (device/'serial').unlink()
    assert run('bind',serial=identity)[0]!=0 and events.read_text()==''
print('PASS USB/IP device action: identity, preflight, ownership, argv, lock FD, busy refusal, observed binding')
