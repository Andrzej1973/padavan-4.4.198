#!/usr/bin/env python3
"""Bind isolated Guest candidate to POST/header/route checks; not production install."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);args=p.parse_args()
httpd=args.source/'trunk/user/httpd';server=httpd/'httpd.c';web=httpd/'web_ex.c'
s=server.read_text();w=web.read_text()
def replace(text,old,new):
 if text.count(old)!=1:p.error('transport anchor changed: '+old[:80])
 return text.replace(old,new,1)
s=replace(s,'static void\nhandle_request(FILE *conn_fp, const conn_item_t *item)', '''#include "wr-shared-wifi/guest-transport.h"
static int wr_modern_guest_post_authorized;
int wr_modern_guest_post_allowed(void) { return wr_modern_guest_post_authorized; }
static void
handle_request(FILE *conn_fp, const conn_item_t *item)''')
s=replace(s,'\t/* Initialize the request variables. */','\tstruct wr_modern_guest_transport modern_transport = {0};\n\twr_modern_guest_post_authorized = 0;\n\t/* Initialize the request variables. */')
s=replace(s,'\t\tif (strncasecmp(cur, "Accept-Language:", 16) == 0) {','\t\tif (strncasecmp(cur, "X-WR-Modern:", 12) == 0) {\n\t\t\twr_modern_guest_header(&modern_transport, cur + 12);\n\t\t}\n\t\telse if (strncasecmp(cur, "Accept-Language:", 16) == 0) {')
# Keep Classic's existing trusted-local behavior, but require actual Basic auth
# for the marked Guest apply even when the inherited login state would skip it.
s=replace(s,'if (handler->need_auth && login_state > 1 && !do_logout)',
 'if (handler->need_auth && !do_logout && (login_state > 1 ||\n\t    (modern_transport.seen && modern_transport.valid && !strcmp(file, "start_apply.htm"))))')
# Bind only after existing authentication and before body/template dispatch.
s=replace(s,'\tif (method_id == HTTP_METHOD_POST) {\n\t\tif (handler->input)','\twr_modern_guest_post_authorized = wr_modern_guest_transport_allowed(\n\t\t&modern_transport, method_id == HTTP_METHOD_POST, file, query);\n\tif (method_id == HTTP_METHOD_POST) {\n\t\tif (handler->input)')
w=replace(w,'#include "wr-shared-wifi/guest-adapter.h"','#include "wr-shared-wifi/guest-adapter.h"\nextern int wr_modern_guest_post_allowed(void);')
w=replace(w,' if(websGetVar(wp,"wr_modern_guest_version",NULL)) {',''' if(websGetVar(wp,"wr_modern_guest_version",NULL)) {
  if(!wr_modern_guest_post_allowed()) {
   websWrite(wp,"Invalid Modern Guest transport. No settings were saved.");
   wr_modern_guest_clear(&modern.guest);return 0;
  }''')
# The isolated bundle also contains main credential admission: apply the same
# transport requirement there before any key read, not just to Guest.
w=replace(w,' if(websGetVar(wp,"wr_modern_wifi_version",NULL)) {',''' if(websGetVar(wp,"wr_modern_wifi_version",NULL)) {
  if(!wr_modern_guest_post_allowed()) {
   websWrite(wp,"Invalid Modern credential transport. No settings were saved.");
   wr_modern_guest_clear(&modern.guest);wr_modern_password_clear(&modern.password);return 0;
  }''')
header=httpd/'wr-shared-wifi/guest-transport.h'
if header.exists():p.error('transport header already exists')
data=(Path(__file__).parent/'guest-transport.h').read_bytes()
header.write_bytes(data);server.write_text(s);web.write_text(w)
print('Prepared isolated Guest POST/header/route gate after inherited authentication; dispatcher acceptance pending')
