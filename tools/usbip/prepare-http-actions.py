#!/usr/bin/env python3
"""Install private asynchronous USB/IP actions behind authenticated POST."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--config',type=Path,required=True)
a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
root=a.source/'trunk/user/httpd'
path=root/'web_ex.c'
text=path.read_text()
anchor='struct mime_handler mime_handlers[] = {'
route='\t{ "update.cgi*",'
entry='\t{ "wr_usbip_inventory", ej_wr_usbip_inventory},\n'
if text.count(anchor)!=1 or text.count(route)!=1 or text.count(entry)!=1 or 'wr_usbip_action_output' in text:
    raise SystemExit('USB/IP action HTTP anchors changed')
here=Path(__file__).parent
main=root/'httpd.c'
main_text=main.read_text()
method_anchor='\tquery = file;'
if main_text.count(method_anchor)!=1 or 'wr_usbip_request_is_post' in main_text:
    raise SystemExit('USB/IP HTTP method anchor changed')
main_text=main_text.replace(method_anchor,'\twr_usbip_method_post = (method_id == HTTP_METHOD_POST);\n'+method_anchor)
include_anchor='#include <stdio.h>'
if main_text.count(include_anchor)!=1:
    raise SystemExit('USB/IP HTTP method declaration anchor changed')
main_text=main_text.replace(include_anchor,include_anchor+'\nstatic int wr_usbip_method_post;\nint wr_usbip_request_is_post(void) { return wr_usbip_method_post; }\n')
text=text.replace(anchor,(here/'http-actions.inc').read_text()+'\n'+anchor)
text=text.replace(route,'\t{ "wr_usbip_action.cgi*", "application/json", no_cache_IE, wr_usbip_action_input, wr_usbip_action_output, 1 },\n'+route)
text=text.replace(entry,entry+'\t{ "wr_usbip_token", ej_wr_usbip_token},\n\t{ "wr_usbip_job_state", ej_wr_usbip_job_state},\n')
(root/'wr-usbip-job.h').write_text((here/'job-worker.h').read_text())
path.write_text(text)
main.write_text(main_text)
print('Prepared safe-session POST/CSRF USB/IP background actions and job observation')
