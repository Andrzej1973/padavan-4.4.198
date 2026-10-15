#!/usr/bin/env python3
"""Execute candidate export preflight against a synthetic sysfs/proc tree."""
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='wr-usbip-device-') as directory:
    root=Path(directory)
    for name in ['sys/bus/usb/devices','sys/class/block','sys/class/net','sys/class/tty','proc/self','dev']:
        (root/name).mkdir(parents=True,exist_ok=True)
    device=root/'sys/bus/usb/devices/1-1'
    device.mkdir()
    (device/'bDeviceClass').write_text('00\n')
    mounts=root/'proc/self/mountinfo'
    swaps=root/'proc/swaps'
    mounts.write_text('')
    swaps.write_text('Filename Type Size Used Priority\n')
    source=Path(__file__).with_name('device-policy.sh').read_text()
    for prefix in ['/sys/','/proc/']:
        source=source.replace(prefix,str(root)+prefix)
    script=root/'check.sh'
    script.write_text('set -eu\n'+source+'\nif wr_usbip_device_check "$1"; then exit 0; else exit 1; fi\n')
    def check(bus,allowed):
        result=subprocess.run(['sh',str(script),bus],capture_output=True,text=True)
        assert (result.returncode==0)==allowed,(bus,result.stdout,result.stderr)
    check('1-1',True)
    for bus in ['../1-1','1-1:1.0','1-1\n2-1','1-','usb1','9-9','1-1;id']:
        check(bus,False)
    (device/'bDeviceClass').write_text('09\n');check('1-1',False)
    (device/'bDeviceClass').write_text('00\n')
    block=device/'block/sda/sda1'
    block.mkdir(parents=True)
    (block/'dev').write_text('8:1\n')
    (root/'sys/class/block/sda1').symlink_to(block)
    check('1-1',True)
    mounts.write_text('22 1 8:1 / /mnt/usb rw - ext4 /dev/sda1 rw\n');check('1-1',False)
    mounts.write_text('')
    swap=root/'dev/sda1';swap.write_text('')
    swaps.write_text('Filename Type Size Used Priority\n'+str(swap)+' partition 1 0 -1\n');check('1-1',False)
    swaps.write_text('Filename Type Size Used Priority\n')
    for group in ['net','tty']:
        member=root/'sys/class'/group/'example'
        member.mkdir()
        (member/'device').symlink_to(device)
        check('1-1',False)
        (member/'device').unlink();member.rmdir()
    mounts.unlink();check('1-1',False)
print('PASS USB/IP candidate preflight: malformed IDs, hubs, mounted partitions, swap, NIC/TTY, missing source')
