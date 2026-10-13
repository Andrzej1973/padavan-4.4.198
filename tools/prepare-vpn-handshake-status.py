#!/usr/bin/env python3
"""Install WR-only periodic handshake observations without request-time commands."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
local=Path(__file__).resolve().parent/'vpn-status'
http=a.source/'trunk/user/httpd'
web=http/'web_ex.c';daemon=http/'httpd.c'
s=web.read_text(encoding='utf-8');d=daemon.read_text(encoding='utf-8')
anchor='struct ej_handler ej_handlers[] =\n'
entry='\t{ "wr_vpn_interface_state", ej_wr_vpn_interface_state},\n'
tick='\t\twr_device_background_tick();'
close='\twr_device_background_close();'
if any(text.count(value)!=1 for text,value in [(s,anchor),(s,entry),(d,tick),(d,close)]) or 'wr_vpn_background_tick' in d:
    raise SystemExit('VPN handshake integration anchors changed; no files written')
code=(local/'http-status.inc').read_text(encoding='utf-8')
s=s.replace(anchor,code+'\n'+anchor).replace(entry,entry+'#if defined(BOARD_WR1200JS)\n\t{ "wr_vpn_handshake_state", ej_wr_vpn_handshake_state},\n#endif\n')
d='#if defined(BOARD_WR1200JS)\nextern void wr_vpn_background_tick(void);\nextern void wr_vpn_background_close(void);\n#endif\n'+d
d=d.replace(tick,tick+'\n\t\twr_vpn_background_tick();').replace(close,close+'\n\twr_vpn_background_close();')
headers=http/'wr-vpn';headers.mkdir(exist_ok=True)
for name in ('handshake-observation.h','handshake-cache.h','handshake-worker.h','handshake-runtime.h'):
    (headers/name).write_bytes((local/name).read_bytes())
web.write_text(s,encoding='utf-8');daemon.write_text(d,encoding='utf-8')
print('Installed WR handshake background sampling and EJ observation; peer keys are not exposed')
