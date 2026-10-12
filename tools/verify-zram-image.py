#!/usr/bin/env python3
"""Check zram build dependencies and shipped BusyBox CLI, not swap activation."""
import argparse
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
trunk = args.source / 'trunk'
if 'CONFIG_FIRMWARE_INCLUDE_ZRAM=y' not in (trunk / '.config').read_text().splitlines():
    print('SKIP: zram excluded by requested profile')
    raise SystemExit(0)
kernel = (trunk / 'linux-4.4.x/.config').read_text().splitlines()
for value in ('CONFIG_SWAP=y', 'CONFIG_ZSMALLOC=y', 'CONFIG_ZRAM=m'):
    if value not in kernel:
        raise SystemExit('FAIL zram kernel dependency: ' + value)
config = (trunk / 'user/busybox/busybox-1.24.x/.config').read_text().splitlines()
for value in ('CONFIG_MKSWAP=y', 'CONFIG_SWAPONOFF=y', 'CONFIG_FEATURE_SWAPON_PRI=y', 'CONFIG_FEATURE_SWAPON_DISCARD=y'):
    if value not in config:
        raise SystemExit('FAIL zram BusyBox dependency: ' + value)
romfs = trunk / 'romfs'
page = (romfs / 'www/Advanced_System_Content.asp').read_text()
if 'wr_zram_state();' not in page or 'id="wr_zram_status"' not in page:
    raise SystemExit('FAIL shipped ZRAM observed-state UI missing')
if b'wr_zram_state' not in (romfs / 'usr/sbin/httpd').read_bytes():
    raise SystemExit('FAIL linked ZRAM status handler missing')
binary = (romfs / 'sbin/rc').read_bytes()
if b'swapon -p 32767 -d /dev/zram0' not in binary:
    raise SystemExit('FAIL shipped rc zram startup command missing')
qemu = shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel')
if not qemu:
    raise SystemExit('FAIL QEMU required for shipped BusyBox check')
result = subprocess.run([qemu, '-L', str(romfs.resolve()), str((romfs / 'bin/busybox').resolve()),
                         'swapon', '--help'], capture_output=True, text=True, timeout=20)
help_text = result.stdout + result.stderr
if '-p PRI' not in help_text or '-d' not in help_text:
    raise SystemExit('FAIL shipped BusyBox does not expose required swapon priority/discard options')
print('PASS zram dependencies, rc command and image BusyBox priority/discard help under QEMU; activation unverified')
