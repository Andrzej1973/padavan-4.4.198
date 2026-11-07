#!/usr/bin/env python3
"""Bind the private IoT channel into a prepared, WR1200JS-only source candidate.

This does not implement activation and must not be called by production image
preparation until the backend and acceptance gates are complete.
"""
import argparse
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
a=p.parse_args()
local=Path(__file__).parent
rc=a.source/'trunk/user/rc'
http=a.source/'trunk/user/httpd'
pending={}

def once(text,anchor,replacement):
    if text.count(anchor)!=1:
        raise SystemExit('IoT control source anchor changed: '+anchor[:70])
    return text.replace(anchor,replacement,1)

rc_make=(rc/'Makefile').read_text(encoding='utf-8')
http_make=(http/'Makefile').read_text(encoding='utf-8')
main=(rc/'rc.c').read_text(encoding='utf-8')
init=(rc/'init.c').read_text(encoding='utf-8')
web=(http/'web_ex.c').read_text(encoding='utf-8')
if 'wr-iot-request-stage.o' not in rc_make or 'wr_iot_http_apply_output' not in web:
    raise SystemExit('Prepare the RC IoT and dedicated HTTP candidates first')
if any('wr-iot-control-' in text for text in (rc_make,http_make)) or 'wr_iot_rc_dispatch' in main:
    raise SystemExit('IoT control candidate already installed')
rc_anchor='OBJS += gpio_btn.o btn_action.o'
rc_make=once(rc_make,rc_anchor,rc_anchor+'''
ifneq ($(findstring -DBOARD_WR1200JS,$(CFLAGS)),)
OBJS += wr-iot-control-mailbox.o wr-iot-control-server.o
endif''')
http_anchor='OBJS += dbapi.o\nall:'
http_make=once(http_make,http_anchor,'''OBJS += dbapi.o
ifneq ($(findstring -DBOARD_WR1200JS,$(CFLAGS)),)
OBJS += wr-iot-control-mailbox.o wr-iot-control-client.o
endif
all:''')
main=once(main,'#include "rc.h"', '''#include "rc.h"
#if defined(BOARD_WR1200JS)
#include "wr-iot/control-channel.h"
#endif''')
init=once(init,'#include "rc.h"', '''#include "rc.h"
#if defined(BOARD_WR1200JS)
#include "wr-iot/rc-shutdown-admission.h"
#endif''')
init=once(init,'catch_sig_fatal(int sig)\n{\n\tsig_term_received = 1;',
 '''catch_sig_fatal(int sig)
{
#if defined(BOARD_WR1200JS)
\t/* Defer only normal shutdown during the owned IoT RC transaction. */
\tif (wr_iot_rc_shutdown_note(sig))
\t\treturn;
#endif
\tsig_term_received = 1;''')
dispatch='\t\tif (!strcmp(entry->d_name, RCN_RESTART_REBOOT))'
main=once(main,dispatch,'''#if defined(BOARD_WR1200JS)
		if (!strcmp(entry->d_name, "wr_iot_apply"))
		{
			wr_iot_rc_dispatch();
		}
		else
#endif
'''+dispatch)
pending[rc/'rc.c']=main.encode()
pending[rc/'init.c']=init.encode()
pending[rc/'Makefile']=rc_make.encode()
pending[http/'Makefile']=http_make.encode()
headers=('control-channel.h','control-mailbox.h','control-record.h','service-lock.h',
         'request.h','subnet.h','types.h')
for root,role in ((rc,'server'),(http,'client')):
    for name in headers:
        path=root/'wr-iot'/name
        expected=(local/name).read_bytes()
        if path.exists() and path.read_bytes()!=expected:
            raise SystemExit('Existing candidate header differs; preserve it: '+str(path))
        pending[path]=expected
    validation=root/'shared-wifi/validate.h'
    expected=(local.parent/'shared-wifi/validate.h').read_bytes()
    if validation.exists() and validation.read_bytes()!=expected:
        raise SystemExit('Existing shared validation differs; preserve it: '+str(validation))
    pending[validation]=expected
    for unit in ('mailbox',role):
        path=root/('wr-iot-control-'+unit+'.c')
        if path.exists():
            raise SystemExit('Existing control unit must not be overwritten: '+str(path))
        text=(local/('control-'+unit+'.c')).read_text(encoding='utf-8')
        for name in ('control-channel.h','control-mailbox.h'):
            text=text.replace('#include "'+name+'"','#include "wr-iot/'+name+'"')
        if role=='server':
            text=text.replace('#include "rc-shutdown-admission.h"',
                              '#include "wr-iot/rc-shutdown-admission.h"')
        pending[path]=text.encode()
pending[rc/'wr-iot/rc-shutdown-admission.h']=(local/'rc-shutdown-admission.h').read_bytes()
for path,data in pending.items():
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
(a.source/'iot-control-source.json').write_text(json.dumps({
 'board':'WR1200JS','http_objects_bound':True,'rc_objects_bound':True,
 'fixed_notification':'wr_iot_apply','activation_backend_installed':False,
 'normal_shutdown_signal_deferred_in_candidate':True,
 'production_ready':False,'runtime_verified':False,
},indent=2)+'\n',encoding='utf-8')
print('Bound IoT channel objects and fixed RC notification; real activation backend still required')
