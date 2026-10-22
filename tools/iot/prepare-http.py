#!/usr/bin/env python3
"""Stage a dedicated IoT CGI candidate; transport is bound separately.

Never invoke in firmware preparation until the complete RC backend and result
path are verified. Pair with prepare-control.py only in a source candidate;
the strong RC activation backend dependency remains deliberately unresolved.
"""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
local = Path(__file__).parent
root = a.source / 'trunk/user/httpd'
main_path, web_path = root / 'httpd.c', root / 'web_ex.c'
main, web = main_path.read_text(encoding='utf-8'), web_path.read_text(encoding='utf-8')

def once(text, anchor, replacement):
    if text.count(anchor) != 1:
        raise SystemExit('IoT HTTP candidate anchor changed: ' + anchor[:65])
    return text.replace(anchor, replacement, 1)

if 'wr_iot_http_' in main or 'wr_iot_http_' in web:
    raise SystemExit('IoT HTTP candidate already installed')
main = once(main, '#include <stdio.h>', '''#include <stdio.h>
#if defined(BOARD_WR1200JS)
static int wr_iot_http_post,wr_iot_http_type_count;
static char wr_iot_http_type[128];
int wr_iot_http_is_post(void) { return wr_iot_http_post; }
const char *wr_iot_http_content_type(void) {
 return wr_iot_http_type_count==1 ? wr_iot_http_type : NULL;
}
#endif
''')
main = once(main, '\tauthorization = boundary = NULL;',
            '\tauthorization = boundary = NULL;\n'
            '#if defined(BOARD_WR1200JS)\n'
            '\twr_iot_http_post=0;wr_iot_http_type_count=0;wr_iot_http_type[0]=0;\n#endif')
header_anchor = '\t\tif (strncasecmp(cur, "Accept-Language:", 16) == 0) {'
main = once(main, header_anchor, '''#if defined(BOARD_WR1200JS)
		/* Independent capture preserves existing multipart boundary parsing. */
		if (strncasecmp(cur, "Content-Type:", 13) == 0) {
			size_t n;char *value=cur+13;
			value+=strspn(value," \\t");n=strcspn(value,"\\r\\n");
			if(wr_iot_http_type_count<2)wr_iot_http_type_count++;
			if(n>0&&n<sizeof(wr_iot_http_type)) {
				memcpy(wr_iot_http_type,value,n);wr_iot_http_type[n]=0;
			} else wr_iot_http_type[0]=0;
		}
#endif
''' + header_anchor)
main = once(main, '\tquery = file;',
            '#if defined(BOARD_WR1200JS)\n\twr_iot_http_post=(method_id==HTTP_METHOD_POST);\n#endif\n\tquery = file;')
handler = (local/'http-handler.inc').read_text(encoding='utf-8').replace(
    '#include "http-request.h"', '#include "wr-iot/http-request.h"', 1)
handler = handler.replace('#include "control-record.h"','#include "wr-iot/control-record.h"',1)
web = once(web, 'struct mime_handler mime_handlers[] = {',
           '#if defined(BOARD_WR1200JS)\n'+handler + '\n#endif\nstruct mime_handler mime_handlers[] = {')
route = '\t{ "update.cgi*",'
web = once(web, route,
           '#if defined(BOARD_WR1200JS)\n'
           '\t{ "wr_iot_token.cgi", "application/json", no_cache_IE, NULL, wr_iot_http_token_output, 1 },\n'
           '\t{ "wr_iot_apply.cgi", "application/json", no_cache_IE, wr_iot_http_apply_input, wr_iot_http_apply_output, 1 },\n'
           '\t{ "wr_iot_result.cgi", "application/json", no_cache_IE, NULL, wr_iot_http_result_output, 1 },\n#endif\n' + route)
validation = root/'shared-wifi/validate.h'
expected = (local.parent/'shared-wifi/validate.h').read_bytes()
if validation.exists() and validation.read_bytes() != expected:
    raise SystemExit('Existing shared Wi-Fi validation differs; preserve it')
headers = root/'wr-iot'
headers.mkdir(exist_ok=True)
for name in ('http-form.h','http-request.h','control-record.h','request.h','subnet.h','types.h'):
    (headers/name).write_bytes((local/name).read_bytes())
(root/'shared-wifi').mkdir(exist_ok=True)
validation.write_bytes(expected)
main_path.write_text(main,encoding='utf-8')
web_path.write_text(web,encoding='utf-8')
print('Prepared authenticated IoT CGI candidate; RC transport/result backend still required')
