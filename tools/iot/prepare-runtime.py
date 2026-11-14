#!/usr/bin/env python3
"""Install RC runtime/status adapters into an experimental prepared tree only.

Requires actual RC, HTTP and control preparation. This is not production image
admission: initial-OFF/reopen and physical acceptance remain separate gates.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
local=Path(__file__).parent;rc=a.source/'trunk/user/rc';http=a.source/'trunk/user/httpd'
if (a.source/'iot-runtime-source.json').exists():raise SystemExit('Runtime candidate already prepared')
control=json.loads((a.source/'iot-control-source.json').read_text())
if control.get('board')!='WR1200JS' or not (rc/'wr-iot/activation-owner.h').is_file():
 raise SystemExit('Full WR RC/control candidates required')
pending={}
def once(text,anchor,replacement):
 if text.count(anchor)!=1:raise SystemExit('Runtime source anchor changed: '+anchor[:60])
 return text.replace(anchor,replacement,1)
init=(rc/'init.c').read_text()
init=once(init,'#include "wr-iot/rc-shutdown-admission.h"','#include "wr-iot/rc-shutdown-admission.h"\n#include "wr-iot/rc-runtime.h"')
init=once(init,'\t\t\t\tsigsuspend(&ss);','''#if defined(BOARD_WR1200JS)
\t\t\t\twr_iot_rc_wait(&ss,&sig_usr1_received,&sig_alrm_received);
#else
\t\t\t\tsigsuspend(&ss);
#endif''')
pending[rc/'init.c']=init.encode()
common=('status-channel','status-endpoint')
for root,units,anchor in ((rc,('rc-backend','rc-mode','rc-runtime','physical-stop-client','physical-stop-down','physical-stop-session','rc-physical-stop','physical-rebind-client','physical-rebind-controller','rebind-start','rebind-network','rebind-rollback','rebind-commit','rebind-close','rebind-closed-rollback','rebind-runner','rebind-active-stop','rebind-observe','rebind-owner','restart-profile','restart-main-state','restart-generation','restart-main-up','restart-main-controller','restart-main-bridge','restart-guest-up','restart-guest-bridge','restart-guest-isolation','restart-guest-controller','restart-services','restart-restore','restart-finish-check','restart-resume','restart-cancel-check','restart-prehandoff-check','restart-resume-retire','restart-scheduler')+common,'wr-iot-control-mailbox.o wr-iot-control-server.o'),(http,('status-client',)+common,'wr-iot-control-mailbox.o wr-iot-control-client.o')):
 text=(root/'Makefile').read_text()
 text=once(text,anchor,anchor+' '+' '.join('wr-iot-'+u+'.o' for u in units));pending[root/'Makefile']=text.encode()
 headers=('status-channel.h','status-endpoint.h','precreated-entropy.h')+(('rc-backend.h','rc-quiesce.h','rc-runtime.h','physical-stop-client.h','physical-stop-down.h','physical-stop-session.h','rc-physical-stop.h','physical-rebind-client.h','physical-rebind-controller.h','rebind-start.h','rebind-network.h','rebind-rollback.h','rebind-commit.h','rebind-close.h','rebind-closed-rollback.h','rebind-runner.h','rebind-active-stop.h','rebind-observe.h','rebind-owner.h','restart-profile.h','restart-main-state.h','restart-generation.h','restart-profile-receipt.h','restart-main-up.h','restart-main-controller.h','restart-main-bridge.h','restart-guest-up.h','restart-guest-policy.h','restart-guest-bridge.h','restart-guest-isolation.h','restart-guest-controller.h','restart-service-policy.h','restart-services.h','restart-restore.h','restart-resume.h','restart-scheduler.h','physical-rebind-wire.h','physical-stop-response.h','physical-stop-wire.h') if root==rc else ())
 for name in headers:
  target=root/'wr-iot'/name;data=(local/name).read_bytes()
  if target.exists() and target.read_bytes()!=data:raise SystemExit('Conflicting runtime header: '+str(target))
  pending[target]=data
 for unit in units:
  text=(local/(unit+'.c')).read_text()
  for header in local.glob('*.h'):
   text=text.replace('#include "'+header.name+'"','#include "wr-iot/'+header.name+'"')
  target=root/('wr-iot-'+unit+'.c')
  if target.exists():raise SystemExit('Refuse to overwrite runtime source: '+str(target))
  pending[target]=text.encode()
for target,data in pending.items():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(a.source/'iot-runtime-source.json').write_text(json.dumps({'board':'WR1200JS','activation_backend_installed':True,'http_private_status_backend_installed':True,'pid1_wait_bound':True,'status_peer_pid':1,'status_peer_uid':0,'progress_period_ms':100,'initial_off_admission':True,'off_reopen_admission':True,'physical_stop_transport_linked':True,'physical_stop_private_quiesce_linked':True,'physical_stop_wait_continuation_bound':True,'physical_stop_rc_entrypoints_bound':False,'rebind_network_helpers_linked':True,'rebind_close_helpers_linked':True,'rebind_runner_linked':True,'rebind_active_off_observer_linked':True,'rebind_backend_routing_linked':True,'rebind_off_reopen_handoff':True,'rebind_repeat_admission':True,'restart_profile_observer_linked':True,'restart_generation_linked':True,'restart_main_controller_linked':True,'restart_main_bridge_linked':True,'restart_resume_progress_bound':True,'restart_resume_begin_bound':True,'restart_resume_linked':True,'restart_resume_bound':False,'restart_restore_linked':True,'restart_restore_bound':False,'restart_services_linked':True,'restart_services_bound':False,'restart_guest_controller_linked':True,'restart_guest_controller_bound':False,'restart_guest_up_linked':True,'restart_guest_down_preparation_linked':True,'physical_stop_restart_resume_bound':False,'physical_stop_rc_orchestration':False,'production_ready':False,'runtime_verified':False},indent=2)+'\n')
print('PASS experimental WR runtime/backend/status sources staged; initial OFF and CLOSED-witness reopen staged; production acceptance unresolved')
