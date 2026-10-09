#!/usr/bin/env python3
"""Install WR-only passive device JSON output through the authenticated MIME table."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
local=Path(__file__).resolve().parent;http=a.source/'trunk/user/httpd';f=http/'web_ex.c';s=f.read_text(encoding='utf-8')
anchor='struct mime_handler mime_handlers[] = {\n'
if s.count(anchor)!=1 or 'do_wr_devices_json' in s:raise SystemExit('HTTP route anchors changed; no files written')
if '{ "update.cgi*", "text/javascript", no_cache_IE, do_html_apply_post, do_update_cgi, 1 }' not in s:raise SystemExit('Pinned authenticated update route changed')
code=(local/'http-hook.inc').read_text(encoding='utf-8')
route='#if defined(BOARD_WR1200JS)\n\t{ "wr_devices.json", "application/json", no_cache_IE, NULL, do_wr_devices_json, 1 },\n#endif\n'
s=s.replace(anchor,code+'\n'+anchor+route,1)
headers=http/'wr-devices';headers.mkdir(exist_ok=True)
for name in ('networkmap.h','source-collector.h','snapshot-cache.h','snapshot-json.h'):(headers/name).write_bytes((local/name).read_bytes())
f.write_text(s,encoding='utf-8')
print('Installed WR-only passive JSON route with need_auth=1; no scanning or service restart')
