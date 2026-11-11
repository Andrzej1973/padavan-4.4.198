#!/usr/bin/env python3
"""Expose an isolated Guest JSON candidate using existing apply/commit/notify code."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);args=p.parse_args()
root=args.source/'trunk/user/httpd';web=root/'web_ex.c';server=root/'httpd.c';header=root/'wr-shared-wifi/guest-transport.h'
w=web.read_text();s=server.read_text();h=header.read_text()
def once(text,old,new):
 if text.count(old)!=1:p.error('JSON anchor changed: '+old[:80])
 return text.replace(old,new,1)
w=once(w,'#include "wr-shared-wifi/guest-adapter.h"','#include "wr-shared-wifi/guest-adapter.h"\nint wr_modern_guest_finish_seen;')
a=w.index('update_variables_ex(');b=w.index('\n}',a)+2;fn=w[a:b]
cleanup='wr_modern_guest_clear(&modern.guest); wr_modern_password_clear(&modern.password); return 0;'
i=fn.rfind(cleanup)
if i<0:p.error('JSON request finish cleanup changed')
fn=fn[:i]+'if(modern.guest_active)wr_modern_guest_finish_seen=1;\n '+fn[i:]
w=w[:a]+fn+w[b:]
anchor='struct mime_handler mime_handlers[] = {\n'
output=(Path(__file__).parent/'guest-json-output.c.inc').read_text()
w=once(w,anchor,output+'\n'+anchor+'\t{ "wr_modern_guest_apply.json", "application/json", no_cache_IE, do_html_apply_post, do_wr_modern_guest_apply, 1 },\n')
s=once(s,'!strcmp(file, "start_apply.htm")','(!strcmp(file, "start_apply.htm") || !strcmp(file, "wr_modern_guest_apply.json"))')
s=once(s,'\tif (wr_modern_guest_post_authorized)\n\t\twr_modern_body_clear();',
 '\tif (wr_modern_guest_post_authorized || !strcmp(file, "wr_modern_guest_apply.json"))\n\t\twr_modern_body_clear();')
h=once(h,'!strcmp(file,"start_apply.htm")','(!strcmp(file,"start_apply.htm")||!strcmp(file,"wr_modern_guest_apply.json"))')
web.write_text(w);server.write_text(s);header.write_text(h)
print('Prepared isolated Guest JSON result route; RAM observation/requests only, runtime unverified')
