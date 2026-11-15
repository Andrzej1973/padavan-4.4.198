#!/usr/bin/env python3
"""Verify exact experimental RC/HTTP runtime sources and board Make selection."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
local=Path(__file__).parent;rc=a.source/'trunk/user/rc';http=a.source/'trunk/user/httpd'
report=json.loads((a.source/'iot-runtime-source.json').read_text())
assert report['radio_off_progress_bound'] and report['radio_off_profile_ram_progress_bound']
assert report['radio_on_root_progress_bound'] and not report['radio_on_entry_bound']
assert report['radio_on_followup_linked']
assert report['radio_on_parent_release_linked']
assert report['radio_on_handoff_linked']
assert report['radio_on_restore_linked'] and report['radio_on_aux_observer_linked'] and report['radio_on_multicast_linked']
assert report['radio_on_guest_linked'] and report['radio_on_services_linked']
assert report['radio_on_generation_linked'] and report['radio_on_main_linked']
assert report['radio_on_admission_linked'] and not report['radio_on_entry_bound']
assert report['radio_off_consumer_linked'] and not report['radio_off_entry_bound']
assert report['board']=='WR1200JS' and report['activation_backend_installed'] and report['pid1_wait_bound']
assert not report['production_ready'] and not report['runtime_verified'] and report['off_reopen_admission']
a.output.mkdir(parents=True,exist_ok=True)
shared=a.output/'make-headers';shared.mkdir(exist_ok=True)
for name in ['boards.mk','cflags.mk']:(shared/name).write_text('')
for root,units in [(rc,['rc-backend','rc-mode','rc-runtime','radio-off-owner','radio-off-observe','radio-on-admission','radio-on-generation','radio-on-main','radio-on-guest','radio-on-services','radio-on-multicast','radio-on-restore','radio-on-handoff','radio-on-release','radio-on-followup','radio-on-owner','radio-on-prehandoff','radio-on-shutdown-check','radio-on-aux','radio-off-profile','radio-off-profile-check','radio-off-followup','radio-off-bridge','radio-off-wan','status-channel','status-endpoint']),(http,['status-client','status-channel','status-endpoint'])]:
 for u in units:
  expected=(local/(u+'.c')).read_text()
  for h in local.glob('*.h'):expected=expected.replace('#include "'+h.name+'"','#include "wr-iot/'+h.name+'"')
  assert (root/('wr-iot-'+u+'.c')).read_text()==expected,u
 for flag,enabled in [('-DBOARD_WR1200JS',True),('-DBOARD_OTHER',False),('',False)]:
  run=subprocess.run(['make','--no-print-directory','-f',str((root/'Makefile').resolve()),'SHDIR='+str(shared.resolve()),'CFLAGS='+flag,'--eval=print_iot_runtime:;@echo $(OBJS)','print_iot_runtime'],check=True,capture_output=True,text=True)
  for u in units:assert (('wr-iot-'+u+'.o') in run.stdout.split())==enabled,(u,flag)
 for name in ['status-channel.h','status-endpoint.h','precreated-entropy.h']+(['rc-backend.h','rc-runtime.h','radio-off-owner.h','radio-off-observe.h','radio-on-admission.h','radio-on-generation.h','radio-on-main.h','radio-on-guest.h','radio-on-services.h','radio-on-multicast.h','radio-on-restore.h','radio-on-handoff.h','radio-on-release.h','radio-on-followup.h','radio-on-owner.h','radio-on-prehandoff.h','radio-on-shutdown-check.h','radio-on-release-runtime.h','radio-on-aux.h','radio-off-profile.h','radio-off-followup.h','radio-off-bridge.h','radio-off-wan.h'] if root==rc else []):
  assert (root/'wr-iot'/name).read_bytes()==(local/name).read_bytes(),name
init=(rc/'init.c').read_text()
anchor='''#if defined(BOARD_WR1200JS)
\t\t\t\twr_iot_rc_wait(&ss,&sig_usr1_received,&sig_alrm_received);
#else
\t\t\t\tsigsuspend(&ss);
#endif'''
assert init.count(anchor)==1
assert init.count('#include "wr-iot/rc-runtime.h"')==1
assert init.count('if (wr_iot_rc_shutdown_note(sig))')==1
probe='''#include <signal.h>
#include <assert.h>
static int calls,legacy;
static void wr_iot_rc_wait(const sigset_t *s,const volatile int *n,const volatile int *a){(void)s;(void)n;(void)a;calls++;}
static int fixture_sigsuspend(const sigset_t *s){(void)s;legacy++;return 0;}
#define sigsuspend fixture_sigsuspend
int main(void){sigset_t ss;sigemptyset(&ss);int sig_usr1_received=0,sig_alrm_received=0;(void)sig_usr1_received;(void)sig_alrm_received;
'''+anchor+'''
#if defined(BOARD_WR1200JS)
 assert(calls==1&&!legacy);
#else
 assert(!calls&&legacy==1);
#endif
return 0;}
'''
(a.output/'wait-branch.c').write_text(probe)
print('PASS exact experimental runtime sources/headers, WR-only objects and retained other-board wait branch; full init target compile separate')
