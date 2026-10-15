#!/usr/bin/env python3
"""Exercise USB/IP Apply source wiring and fail-before-write guards."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--workspace', type=Path)
a = p.parse_args()
temporary = tempfile.TemporaryDirectory() if a.workspace is None else None
base = a.workspace or Path(temporary.name)
base.mkdir(parents=True, exist_ok=True)
root = base / 'trunk/user'
files = {
 'httpd/common.h': '#define EVM_RESTART_FIREWALL (1ULL << 0)\n#define EVT_RESTART_SPOOLER 1\n',
 'shared/notify_rc.h': '#define RCN_RESTART_IPERF3 "restart_iperf3"\n',
 'httpd/variables.c': '#if defined(APP_IPERF3)\n\t\t\t{"iperf3_enable", "", NULL, EVM_RESTART_IPERF3},\n#endif\n#if defined(APP_IPERF3)\n\t\t{EVM_RESTART_IPERF3, EVT_RESTART_IPERF3, RCN_RESTART_IPERF3, 0},\n#endif\n',
 'rc/rc.c': '\t\t\trestart_usb_printer_spoolers();\n',
 'www/n56u_ribbon_fixed/Advanced_Printer_others.asp': '                                        <tr><th><#WRUSBIPCore#></th></tr>\n',
 'www/dict/EN.footer': '', 'www/dict/UK.dict': '', 'www/dict/RU.dict': '',
}
for name, text in files.items():
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
config = base / 'profile.config'
script = Path(__file__).with_name('prepare-web.py').resolve()
def run(ok):
    result = subprocess.run([sys.executable, str(script), str(base), '--config', str(config)], capture_output=True, text=True)
    assert (result.returncode == 0) == ok, result.stdout + result.stderr
def snapshot():
    return {name: (root/name).read_text() for name in files}
config.write_text('CONFIG_FIRMWARE_INCLUDE_USBIP=n\n')
run(True)
assert snapshot() == files
config.write_text('CONFIG_FIRMWARE_INCLUDE_USBIP=y\n')
common = root / 'httpd/common.h'
common.write_text(files['httpd/common.h'] + '#define FOREIGN (1ULL << 55)\n')
before = snapshot()
run(True)
assert '#define FOREIGN (1ULL << 55)' in common.read_text()
assert '#define EVT_RESTART_SPOOLER 25' in common.read_text()
for name, text in files.items():
    (root/name).write_text(text)
common.write_text(files['httpd/common.h'])
run(True)
after = snapshot()
assert '"usbip_enable", "", NULL, EVM_RESTART_SPOOLER' in after['httpd/variables.c']
assert 'eval("/usr/sbin/wr-usbip", "reconcile")' in after['rc/rc.c']
assert 'name="usbip_enable"' in after['www/n56u_ribbon_fixed/Advanced_Printer_others.asp']
for name in ['EN.footer', 'UK.dict', 'RU.dict']:
    assert 'WRUSBIPEnableNote=' in after['www/dict/'+name]
run(False)
assert snapshot() == after
if temporary is not None:
    temporary.cleanup()
print('USB/IP Apply fixture passed: disabled, occupied bit preserved, wiring, labels, duplicate rejection')
