#!/usr/bin/env python3
"""Attach read-only EoIP observations to authenticated update.cgi and HTTP ticks."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--config', type=Path, required=True)
a = p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_EOIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
here = Path(__file__).resolve().parent
http = a.source / 'trunk/user/httpd'
web = http / 'web_ex.c'
daemon = http / 'httpd.c'
w, d = web.read_text(), daemon.read_text()
anchor = 'struct ej_handler ej_handlers[] =\n'
entry = '\t{ "wr_vpn_status", ej_wr_vpn_status},\n'
tick = '\t\twr_vpn_background_tick();'
close = '\twr_vpn_background_close();'
for text, token in [(w, anchor), (w, entry), (d, tick), (d, close)]:
    if text.count(token) != 1:
        raise SystemExit('EoIP HTTP status anchor changed; no files written')
if 'wr_eoip_background_tick' in d or 'ej_wr_eoip_status' in w:
    raise SystemExit('EoIP status already integrated')
w = w.replace(anchor, (here / 'http-status.inc').read_text() + '\n' + anchor)
w = w.replace(entry, entry + '#if defined(APP_EOIP)\n\t{ "wr_eoip_status", ej_wr_eoip_status},\n#endif\n')
d = ('#if defined(BOARD_WR1200JS) && defined(APP_EOIP)\n'
     'extern void wr_eoip_background_tick(void);\nextern void wr_eoip_background_close(void);\n#endif\n') + d
d = d.replace(tick, tick + '\n#if defined(APP_EOIP)\n\t\twr_eoip_background_tick();\n#endif')
d = d.replace(close, close + '\n#if defined(APP_EOIP)\n\twr_eoip_background_close();\n#endif')
headers = http / 'wr-eoip'
headers.mkdir(exist_ok=True)
for name in ('observation.h', 'netlink-query.h', 'status-runtime.h'):
    (headers / name).write_bytes((here / name).read_bytes())
web.write_text(w)
daemon.write_text(d)
print('Prepared on-demand background EoIP observations; authenticated EJ route only')
