#!/usr/bin/env python3
"""Bind strict marked Modern POST bodies to existing CGI; isolated candidate only."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);args=p.parse_args()
root=args.source/'trunk/user/httpd';server=root/'httpd.c';web=root/'web_ex.c';cgi=root/'cgi.c'
s=server.read_text();w=web.read_text();c=cgi.read_text()
if '{ "**.htm*", "text/html", no_cache_IE, do_html_apply_post, do_ej, 1 }' not in w:
 p.error('authenticated HTM body/template route changed')
def replace(text,old,new):
 if text.count(old)!=1:p.error('body anchor changed: '+old[:80])
 return text.replace(old,new,1)
s=replace(s,'#include "wr-shared-wifi/guest-transport.h"','#include "wr-shared-wifi/guest-transport.h"\n#include "wr-shared-wifi/modern-body.h"\nextern void wr_modern_body_clear(void);')
s=replace(s,'static int wr_modern_guest_post_authorized;','static int wr_modern_guest_post_authorized;\nstatic int wr_modern_input_rejected;\nvoid wr_modern_guest_input_fail(void) { wr_modern_input_rejected = 1; }')
s=replace(s,'\tstruct wr_modern_guest_transport modern_transport = {0};','\tstruct wr_modern_guest_transport modern_transport = {0};\n\tint modern_lengths = 0, modern_length_ok = 0, modern_transfer = 0;\n\twr_modern_input_rejected = 0;')
s=replace(s,'\t\t\tclen = strtoul( cp, NULL, 0 );','\t\t\tmodern_lengths++;modern_length_ok = wr_modern_content_length(cp);\n\t\t\tclen = strtoul( cp, NULL, 0 );')
s=replace(s,'\t\telse if (strncasecmp( cur, "If-Modified-Since:", 18) == 0) {','\t\telse if (strncasecmp(cur, "Transfer-Encoding:", 18) == 0) {\n\t\t\tmodern_transfer = 1;\n\t\t}\n\t\telse if (strncasecmp( cur, "If-Modified-Since:", 18) == 0) {')
s=replace(s,'\tif (method_id == HTTP_METHOD_POST) {\n\t\tif (handler->input)','''	if (wr_modern_guest_post_authorized &&
	    (modern_lengths != 1 || !modern_length_ok || modern_transfer)) {
		send_error(400, "Bad Request", NULL, "Invalid Modern body framing.", conn_fp);return;
	}
	if (method_id == HTTP_METHOD_POST) {
		if (handler->input)''')
s=replace(s,'\t\ttry_pull_data(conn_fp, item->fd);','\t\tif (wr_modern_input_rejected) {\n\t\t\tsend_error(400, "Bad Request", NULL, "Invalid Modern body.", conn_fp);return;\n\t\t}\n\t\ttry_pull_data(conn_fp, item->fd);')
s=replace(s,'\tif (do_logout)\n\t\thttp_logout(&conn_ip);','\tif (wr_modern_guest_post_authorized)\n\t\twr_modern_body_clear();\n\tif (do_logout)\n\t\thttp_logout(&conn_ip);')
w=replace(w,'extern int wr_modern_guest_post_allowed(void);','extern int wr_modern_guest_post_allowed(void);\nextern void wr_modern_guest_input_fail(void);\n#include "wr-shared-wifi/modern-body.h"')
a='do_html_apply_post(const char *url, FILE *stream, int clen, char *boundary)\n{'
w=replace(w,a,a+'''
	if (wr_modern_guest_post_allowed()) {
		init_cgi(NULL);group_del_map[0] = -1;
		if (!wr_modern_body_read(stream, post_buf, sizeof(post_buf), clen)) {
			wr_modern_guest_input_fail();return;
		}
		init_cgi(post_buf);return;
	}''')
w+='''
void wr_modern_body_clear(void)
{
 volatile unsigned char *cursor=(volatile unsigned char *)post_buf;
 size_t i;
 init_cgi(NULL);
 for(i=0;i<sizeof(post_buf);i++)cursor[i]=0;
}
'''
c=replace(c,'strncpy(s, s + 2, strlen(s) + 1);','memmove(s, s + 2, strlen(s + 2) + 1);')
headers={n:(Path(__file__).parent/n).read_bytes() for n in ['modern-form.h','modern-body.h']}
for n in headers:
 if (root/'wr-shared-wifi'/n).exists():p.error('body header exists: '+n)
for n,b in headers.items():(root/'wr-shared-wifi'/n).write_bytes(b)
server.write_text(s);web.write_text(w);cgi.write_text(c)
print('Prepared isolated Modern exact-body/CGI gate and valid-percent memmove correction; not production')
