#!/usr/bin/env python3
"""Verify installed channel sources and actual Makefile board selection.

Produce a fixture containing the installed fixed RC dispatch branch. Its
backend is a call counter, not network activation or device acceptance.
"""
import argparse
import json
import subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--make',default='make')
a=p.parse_args()
local=Path(__file__).parent
report=json.loads((a.source/'iot-control-source.json').read_text())
assert report['board']=='WR1200JS' and report['fixed_notification']=='wr_iot_apply'
assert report['http_objects_bound'] and report['rc_objects_bound']
assert report['normal_shutdown_signal_deferred_in_candidate'] is True
assert not report['production_ready'] and not report['activation_backend_installed']
a.output.parent.mkdir(parents=True,exist_ok=True)
shared=a.output.parent/'iot-make-headers'
shared.mkdir(exist_ok=True)
for name in ('boards.mk','cflags.mk'):
    path=shared/name
    if path.exists() and path.read_bytes():
        raise SystemExit('Refuse to replace nonempty Make probe header: '+str(path))
    path.write_text('',encoding='utf-8')
for role,directory in (('server','rc'),('client','httpd')):
    root=a.source/'trunk/user'/directory
    make=root/'Makefile'
    text=make.read_text()
    objects=['wr-iot-control-mailbox.o','wr-iot-control-'+role+'.o']
    for obj in objects:
        assert text.count(obj)==1 and text.index(obj)<text.index('\nall:')
    for flags,enabled in (('-DBOARD_WR1200JS',True),('-DBOARD_OTHER',False),('',False)):
        run=subprocess.run([a.make,'--no-print-directory','-f',str(make.resolve()),
            'SHDIR='+shared.resolve().as_posix(),'CFLAGS='+flags,
            '--eval=print_iot_objects:;@echo $(OBJS)','print_iot_objects'],
            check=True,text=True,capture_output=True)
        words=run.stdout.split()
        assert all((obj in words)==enabled for obj in objects),(directory,flags,run.stdout)
    for unit in ('mailbox',role):
        expected=(local/('control-'+unit+'.c')).read_text()
        for name in ('control-mailbox.h','control-channel.h'):
            expected=expected.replace('#include "'+name+'"','#include "wr-iot/'+name+'"')
        if role=='server':
            expected=expected.replace('#include "rc-shutdown-admission.h"',
                                      '#include "wr-iot/rc-shutdown-admission.h"')
        assert (root/('wr-iot-control-'+unit+'.c')).read_text()==expected
init=(a.source/'trunk/user/rc/init.c').read_text()
shutdown_header=a.source/'trunk/user/rc/wr-iot/rc-shutdown-admission.h'
assert shutdown_header.read_bytes()==(local/'rc-shutdown-admission.h').read_bytes()
assert init.count('#include "wr-iot/rc-shutdown-admission.h"')==1
assert init.count('if (wr_iot_rc_shutdown_note(sig))')==1
fatal=init[init.index('catch_sig_fatal(int sig)'):init.index('catch_sig_event(int sig)')]
assert fatal.index('if (wr_iot_rc_shutdown_note(sig))')<fatal.index('sig_term_received = 1;')
main=(a.source/'trunk/user/rc/rc.c').read_text()
needle='\t\tif (!strcmp(entry->d_name, "wr_iot_apply"))'
assert main.count(needle)==1 and main.count('\t\t\twr_iot_rc_dispatch();')==1
start=main.rfind('#if defined(BOARD_WR1200JS)',0,main.index(needle))
end=main.index('\t\tif (!strcmp(entry->d_name, RCN_RESTART_REBOOT))',start)
branch=main[start:end]
assert branch.endswith('#endif\n')
a.output.write_text('''#include <assert.h>
#include <stdio.h>
#include <string.h>
static int calls,reboots;
int wr_iot_rc_dispatch(void){calls++;return 1;}
struct entry {const char *d_name;};
static void dispatch(const char *name){
 struct entry value={name};struct entry *entry=&value;
'''+branch+'''
 if(!strcmp(entry->d_name,"restart_reboot")){reboots++;}
}
int main(void){
 dispatch("wr_iot_apply");
#if defined(BOARD_WR1200JS)
 assert(calls==1);
#else
 assert(calls==0);
#endif
 assert(!reboots);dispatch("wr_iot_apply_suffix");dispatch("unrelated");
#if defined(BOARD_WR1200JS)
 assert(calls==1);
#else
 assert(calls==0);
#endif
 dispatch("restart_reboot");assert(reboots==1);
 puts("PASS installed IoT dispatch: exact event, board guard and retained reboot branch");
 return 0;
}
''',encoding='utf-8')
print('PASS installed IoT source identities and actual Makefile WR/other/no-board object selection')
