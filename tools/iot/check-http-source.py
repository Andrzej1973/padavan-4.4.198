#!/usr/bin/env python3
"""Extract the installed metadata capture into an executable C fixture."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
root=a.source/'trunk/user/httpd'
main=(root/'httpd.c').read_text(encoding='utf-8')
web=(root/'web_ex.c').read_text(encoding='utf-8')
for route,handler,input_handler in (
 ('wr_iot_token.cgi','wr_iot_http_token_output','NULL'),
 ('wr_iot_apply.cgi','wr_iot_http_apply_output','wr_iot_http_apply_input'),
 ('wr_iot_result.cgi','wr_iot_http_result_output','NULL')):
    entry='{ "'+route+'", "application/json", no_cache_IE, '+input_handler+', '+handler+', 1 }'
    if web.count(entry)!=1:
        raise SystemExit('Missing exact authenticated IoT route: '+route)
handler=(Path(__file__).parent/'http-handler.inc').read_text(encoding='utf-8').replace(
    '#include "http-request.h"','#include "wr-iot/http-request.h"',1)
handler=handler.replace('#include "control-record.h"','#include "wr-iot/control-record.h"',1)
if web.count(handler)!=1:
    raise SystemExit('Installed IoT handler differs from fixture source')
if web.count('#if defined(BOARD_WR1200JS)\n'+handler+'\n#endif')!=1:
    raise SystemExit('IoT HTTP implementation must be guarded for its board')
route_start=web.index('\t{ "wr_iot_token.cgi",')
assert web[:route_start].endswith('#if defined(BOARD_WR1200JS)\n')
route_end=web.index('\n',web.index('\t{ "wr_iot_result.cgi",',route_start))
assert web[route_end:].startswith('\n#endif\n')
start=main.index('static int wr_iot_http_post,wr_iot_http_type_count;')
assert main[:start].endswith('#if defined(BOARD_WR1200JS)\n')
end=main.index('\n}\n',start)+3
assert main[end:].startswith('#endif\n')
declarations=main[start:end]
reset_begin=main.index('static void\nreset_login_data(void)')
reset_end=main.index('\n}',reset_begin)
reset_body=main[reset_begin:reset_end]
if reset_body.count('#if defined(BOARD_WR1200JS)\n\twr_iot_http_session_reset();\n#endif')!=1:
    raise SystemExit('IoT session token/body must reset with HTTPD login state')
if declarations.count('extern void wr_iot_http_session_reset(void);')!=1:
    raise SystemExit('IoT HTTPD session reset declaration missing')
start=main.index('\t\t/* Independent capture preserves existing multipart boundary parsing. */')
end=main.index('\t\tif (strncasecmp(cur, "Accept-Language:", 16) == 0) {',start)
capture=main[start:end]
assert main[:start].endswith('#if defined(BOARD_WR1200JS)\n')
assert capture.endswith('#endif\n')
capture=capture[:-len('#endif\n')]
if main.index('if (handler->need_auth')>main.index('handler->input(file, conn_fp, clen, boundary);'):
    raise SystemExit('HTTP authentication no longer precedes body input')
reset='wr_iot_http_post=0;wr_iot_http_type_count=0;wr_iot_http_type[0]=0;'
post='wr_iot_http_post=(method_id==HTTP_METHOD_POST);'
if main.count(reset)!=1 or main.count(post)!=1:
    raise SystemExit('IoT metadata reset/method observation missing')
for statement in (reset,post):
    assert '#if defined(BOARD_WR1200JS)\n\t'+statement+'\n#endif' in main
a.output.write_text('''#include <assert.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#define HTTP_METHOD_POST 2
'''+declarations+'''
static void reset_request(int method_id){
'''+reset+post+'''
}
static void capture_header(char *cur){
'''+capture+'''
}
int main(void){
 char good[]="Content-Type: application/x-www-form-urlencoded\\r\\n";
 char duplicate[]="Content-Type: application/json\\r\\n";
 char multipart[]="Content-Type: multipart/form-data; boundary=abc\\r\\n";
 char empty[]="Content-Type: \\r\\n";
 reset_request(2);assert(wr_iot_http_is_post()&&!wr_iot_http_content_type());
 capture_header(good);assert(!strcmp(wr_iot_http_content_type(),"application/x-www-form-urlencoded"));
 capture_header(duplicate);assert(!wr_iot_http_content_type());
 capture_header(good);assert(!wr_iot_http_content_type());
 reset_request(0);assert(!wr_iot_http_is_post()&&!wr_iot_http_content_type());
 capture_header(multipart);assert(strstr(multipart,"boundary=abc"));
 reset_request(2);capture_header(empty);assert(!*wr_iot_http_content_type());
 puts("PASS installed IoT metadata: method/reset, exact auth routes, duplicate MIME refusal, boundary preservation");
 return 0;
}
''',encoding='utf-8')
print('Prepared fixture from installed IoT HTTP metadata and checked protected routes')
