#!/usr/bin/env python3
"""Connect the selected USB/IP package to default-off boot/shutdown handling."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--config', type=Path, required=True)
a = p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    print('USB/IP not selected; lifecycle unchanged')
    raise SystemExit(0)

root = a.source / 'trunk/user'
changes = {
    'shared/cflags.mk': [(
        'ifeq ($(CONFIG_FIRMWARE_INCLUDE_IPERF3),y)\n',
        'ifeq ($(CONFIG_FIRMWARE_INCLUDE_USBIP),y)\nCFLAGS += -DAPP_USBIP\nendif\n\n')],
    'shared/defaults.c': [(
        '#if defined (APP_IPERF3)\n',
        '#if defined(APP_USBIP)\n\t{ "usbip_enable", "0" },\n#endif\n\n')],
    'rc/services.c': [(
        '\tstart_iperf3();\n#endif\n',
        '#if defined(APP_USBIP)\n'
        '\tif (nvram_match("usbip_enable", "1")) {\n'
        '\t\tif (eval("/usr/sbin/wr-usbip", "start") != 0)\n'
        '\t\t\tlogmessage("USB/IP", "Startup failed; see wr-usbip log");\n'
        '\t}\n#endif\n'), (
        '\tstop_iperf3();\n#endif\n',
        '#if defined(APP_USBIP)\n'
        '\tif (eval("/usr/sbin/wr-usbip", "stop") != 0)\n'
        '\t\tlogmessage("USB/IP", "Stop unconfirmed; policy retained");\n'
        '#endif\n')],
}
prepared = []
for name, entries in changes.items():
    path = root / name
    text = path.read_text()
    if 'APP_USBIP' in text:
        raise SystemExit('USB/IP lifecycle already present: ' + name)
    for anchor, addition in entries:
        if text.count(anchor) != 1:
            raise SystemExit('USB/IP lifecycle anchor changed: ' + name)
        # Insert selectors/defaults before their peer; calls after the peer.
        replacement = addition + anchor if name.startswith('shared/') else anchor + addition
        text = text.replace(anchor, replacement)
    prepared.append((path, text))
for path, text in prepared:
    path.write_text(text)
print('Prepared default-off USB/IP boot/shutdown integration')
