#!/usr/bin/env python3
"""Check shipped handshake pages, dictionaries and linked utility paths; not runtime."""
import argparse
import os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);a=p.parse_args()
www=a.romfs/'www'
ui=Path(__file__).with_name('handshake-ui.js').read_text(encoding='utf-8')
for name,role in [('vpncli.asp','client'),('vpnsrv.asp','server')]:
    page=(www/name).read_text(encoding='utf-8')
    for marker in [ui,'id="wr_vpn_handshake_status"','arg0:"'+role+'"','output:"wr_vpn_handshake_state"','window.setInterval(wrHSRefresh,30000)','document.hidden']:
        if marker not in page:raise SystemExit('FAIL shipped handshake page: '+name+' missing '+marker[:70])
for name in ['EN.dict','UK.dict','RU.dict']:
    content=(www/name).read_text(encoding='utf-8')
    for key in ['WRHSUnknown','WRHSStale','WRHSPeers','WRHSNote','WRHSRefresh']:
        if content.count('\n'+key+'=')!=1:raise SystemExit('FAIL shipped handshake translation: '+name+' '+key)
binary=(a.romfs/'usr/sbin/httpd').read_bytes()
for marker in [b'wr_vpn_handshake_state',b'/usr/bin/wg',b'latest-handshakes',b'sample_age',b'youngest_age']:
    if marker not in binary:raise SystemExit('FAIL linked handshake observer marker: '+repr(marker))
tool=a.romfs/'usr/bin/wg'
if tool.is_symlink():
    target=os.readlink(tool)
    tool=(a.romfs/target.lstrip('/')) if target.startswith('/') else tool.parent/target
if not tool.is_file() or not os.access(tool,os.X_OK):raise SystemExit('FAIL shipped handshake utility missing or not executable')
print('PASS shipped handshake UI, EN/UK/RU labels and linked observer/utility paths; runtime unverified')
