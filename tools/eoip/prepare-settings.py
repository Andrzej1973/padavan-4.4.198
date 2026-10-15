#!/usr/bin/env python3
"""Install safe-session POST/CSRF EoIP settings through an independent route."""
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
web, main = http / 'web_ex.c', http / 'httpd.c'
w, m = web.read_text(), main.read_text()
anchor = 'struct mime_handler mime_handlers[] = {'
route = '\t{ "update.cgi*",'
entry = '\t{ "wr_eoip_status", ej_wr_eoip_status},\n'
method = '\tquery = file;'
include = '#include <stdio.h>'
for text, token in [(w, anchor), (w, route), (w, entry), (m, method), (m, include)]:
    if text.count(token) != 1:
        raise SystemExit('EoIP settings anchor changed; no files written')
if 'wr_eoip_settings_output' in w or 'wr_eoip_request_is_post' in m:
    raise SystemExit('EoIP settings already integrated')
w = w.replace(anchor, (here / 'http-settings.inc').read_text() + '\n' + anchor)
w = w.replace(route, '#if defined(BOARD_WR1200JS) && defined(APP_EOIP)\n'
    '\t{ "wr_eoip_settings.cgi*", "application/json", no_cache_IE, wr_eoip_settings_input, wr_eoip_settings_output, 1 },\n#endif\n' + route)
w = w.replace(entry, entry + '\t{ "wr_eoip_token", ej_wr_eoip_token},\n')
declarations = ('\n#if defined(BOARD_WR1200JS) && defined(APP_EOIP)\n'
                'static int wr_eoip_method_post;\n'
                'int wr_eoip_request_is_post(void) { return wr_eoip_method_post; }\n#endif\n')
m = m.replace(include, include + declarations)
m = m.replace(method, '#if defined(BOARD_WR1200JS) && defined(APP_EOIP)\n'
    '\twr_eoip_method_post = (method_id == HTTP_METHOD_POST);\n#endif\n' + method)
headers = http / 'wr-eoip'
headers.mkdir(exist_ok=True)
for name in ('config.h', 'table.h', 'settings.h', 'runtime-state.h'):
    (headers / name).write_bytes((here / name).read_bytes())
web.write_text(w); main.write_text(m)
print('Prepared authenticated safe-session EoIP settings POST with token and independent rc notification')
