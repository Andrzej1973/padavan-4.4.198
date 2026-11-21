#!/usr/bin/env python3
"""Install RC runtime/status adapters into an experimental prepared tree only.

Requires actual RC, HTTP and control preparation. This is not production image
admission: initial-OFF/reopen and physical acceptance remain separate gates.
"""
import argparse,json,runpy
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path)
p.add_argument('--native-trunk',type=Path)
a=p.parse_args()
local=Path(__file__).parent;rc=a.source/'trunk/user/rc';http=a.source/'trunk/user/httpd'
if (a.source/'iot-runtime-source.json').exists():raise SystemExit('Runtime candidate already prepared')
control=json.loads((a.source/'iot-control-source.json').read_text())
if control.get('board')!='WR1200JS' or not (rc/'wr-iot/activation-owner.h').is_file():
 raise SystemExit('Full WR RC/control candidates required')
try:
 snapshot=runpy.run_path(str(local/'config-snapshot-guard.py'))['verify'](a.native_trunk or a.source/'trunk',rc)
except (ValueError,OSError) as error:
 if a.native_trunk:raise SystemExit(str(error))
 snapshot={'verified':False,'reason':str(error)}
pending={}
pending[rc/'ralink.c']=runpy.run_path(str(local/'generation-selector-source.py'))['bind']((rc/'ralink.c').read_text()).encode()
pending[rc/'wr-iot/config-snapshot-prepared.h']=runpy.run_path(str(local/'config-snapshot-guard.py'))['marker'](snapshot).encode()
try:
 flash_readback=runpy.run_path(str(local/'native-flash-source-guard.py'))['verify'](a.native_trunk or a.source/'trunk')
except (ValueError,OSError) as error:
 flash_readback={'verified':False,'reason':str(error)}
pending[rc/'wr-iot/native-flash-prepared.h']=runpy.run_path(str(local/'native-flash-source-guard.py'))['marker'](flash_readback).encode()
pending[rc/"wr-iot/restart-iapp-policy.h"]=b"#define WR_IOT_IAPP_POLICY_PREPARED 0\n"
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
# Keep ordinary notification flags queued while a routed shutdown drains.
# This exact pinned loop anchor is required; absence refuses preparation.
init=once(init,'\t\twhile ( !sig_usr1_received &&\n\t\t\t!sig_alrm_received ) {','''#if defined(BOARD_WR1200JS)
\t\twhile ((!sig_usr1_received && !sig_alrm_received) || wr_iot_rc_normal_shutdown_pending()) {
\t\t\tif (wr_iot_rc_normal_shutdown_pending())
\t\t\t\twr_iot_rc_wait(&ss,&sig_usr1_received,&sig_alrm_received);
\t\t\telse
#else
\t\twhile ( !sig_usr1_received &&
\t\t\t!sig_alrm_received ) {
#endif''')
# Each admitted synchronous notification finishes before process-context
# shutdown progression. No long-lived signal mask crosses Wi-Fi owner creation.
usr='\t\tif (sig_usr1_received) {\n\t\t\tsig_usr1_received = 0;\n\t\t\thandle_notifications();\n\t\t}'
usr_new='\n'.join(('#if defined(BOARD_WR1200JS)','\t\tif (sig_usr1_received && wr_iot_rc_normal_notification_begin()) {','#else','\t\tif (sig_usr1_received) {','#endif','\t\t\tsig_usr1_received = 0;','\t\t\thandle_notifications();','#if defined(BOARD_WR1200JS)','\t\t\twr_iot_rc_normal_notification_end();','#endif','\t\t}'))
init=once(init,usr,usr_new)
alarm='\t\tif (sig_alrm_received) {\n\t\t\tsig_alrm_received = 0;\n#if defined (USE_USB_SUPPORT) || defined (USE_STORAGE)\n\t\t\ton_deferred_hotplug_dev();\n#endif\n\t\t}'
alarm_new='\n'.join(('#if defined(BOARD_WR1200JS)','\t\tif (sig_alrm_received && wr_iot_rc_normal_notification_begin()) {','#else','\t\tif (sig_alrm_received) {','#endif','\t\t\tsig_alrm_received = 0;','#if defined (USE_USB_SUPPORT) || defined (USE_STORAGE)','\t\t\ton_deferred_hotplug_dev();','#endif','#if defined(BOARD_WR1200JS)','\t\t\twr_iot_rc_normal_notification_end();','#endif','\t\t}'))
init=once(init,alarm,alarm_new)
init=once(init,'#include "wr-iot/rc-runtime.h"','#include "wr-iot/rc-runtime.h"\n#include "wr-iot/rc-boot.h"\n#include "wr-iot/rc-normal-shutdown.h"\n#include "wr-iot/restart-iapp-policy.h"')
save_startup = '\tinit_router();\n#if defined(BOARD_WR1200JS)\n\t(void)wr_iot_rc_save_backend_install();\n\t(void)wr_iot_rc_edit_backend_install();\n\t(void)wr_iot_rc_view_runtime_install();\n#endif\n#if defined(BOARD_WR1200JS) && WR_IOT_IAPP_POLICY_PREPARED\n\twr_iot_rc_boot_arm();\n#endif'
init=once(init,'\tinit_router();',save_startup)
init=once(init,'#include "wr-iot/rc-runtime.h"','#include "wr-iot/rc-runtime.h"\n#include "wr-iot/config-save-server.h"\n#include "wr-iot/config-edit-server.h"\n#include "wr-iot/config-view-runtime.h"')
pending[rc/'init.c']=init.encode()
common=('status-channel','status-endpoint','config-view-channel','config-view-endpoint')
for root,units,anchor in ((rc,('config-server','config-owner','saved-config-store','native-flash-reader','flash-save-attempt','flash-save-native','flash-worker','config-save-owner','config-save-server','rc-backend','rc-mode','rc-runtime','physical-stop-client','physical-stop-down','physical-stop-session','physical-initial-client','physical-initial-session','rc-initial-stop','rc-physical-stop','physical-rebind-client','physical-rebind-controller','rebind-start','rebind-network','rebind-rollback','rebind-commit','rebind-close','rebind-closed-rollback','rebind-runner','rebind-active-stop','rebind-observe','rebind-owner','initial-restart-select','restart-initial-parent','restart-initial-handoff','restart-profile','restart-main-state','restart-generation','restart-main-up','restart-main-controller','restart-main-bridge','restart-guest-up','restart-guest-bridge','restart-guest-isolation','restart-guest-controller','restart-services','restart-restore','restart-finish-check','restart-resume','restart-cancel-check','restart-prehandoff-check','restart-resume-retire','restart-scheduler','restart-auth-stop','restart-multicast','restart-multicast-controller','restart-iapp-child','restart-wan-followup','restart-terminal-iapp','radio-off-owner','radio-off-observe','radio-on-admission','radio-on-generation','radio-on-main','radio-on-guest','radio-on-services','radio-on-multicast','radio-on-restore','radio-on-disabled','precreated-down-client','precreated-down-observe','cold-on-admission','cold-on-generation','precreated-down-recovery','cold-on-recovery','cold-on-main','cold-on-guest','cold-on-services','cold-on-multicast','cold-on-owner','cold-on-handoff','cold-on-release','cold-on-policy','cold-on-disabled','cold-on-disabled-release','cold-on-prehandoff','cold-on-shutdown','cold-on-postshutdown','cold-on-root','cold-on-root-shutdown','cold-on-root-recovery','cold-on-root-signal','cold-on-scheduler','cold-on-select','cold-on-entry','rc-boot','rc-normal-shutdown','radio-on-handoff','radio-on-release','radio-on-followup','radio-on-owner','radio-on-prehandoff','radio-on-shutdown-check','radio-on-shutdown','radio-on-aux','radio-off-profile','radio-off-profile-check','radio-off-followup','radio-off-bridge','radio-off-wan')+common,'wr-iot-control-mailbox.o wr-iot-control-server.o'),(http,('status-client',)+common,'wr-iot-control-mailbox.o wr-iot-control-client.o')):
 text=(root/'Makefile').read_text()
 if root==rc:units=('config-edit-server','config-view-runtime')+units
 if root==http:units=('config-view-client',)+units
 text=once(text,anchor,anchor+' '+' '.join('wr-iot-'+u+'.o' for u in units))
 if root==rc:
  text+='\nwr-iot-native-flash-reader.o wr-iot-flash-save-native.o: override CFLAGS += -I$(ROOTDIR)/linux-4.4.x/include/nvram\n'
 pending[root/'Makefile']=text.encode()
 headers=('status-channel.h','status-endpoint.h','precreated-entropy.h')+(('radio-off-wan.h','radio-off-auth.h','radio-off-bridge.h','radio-off-followup.h','radio-off-profile.h','radio-off-observe.h','radio-on-admission.h','radio-on-generation.h','radio-on-main.h','radio-on-guest.h','radio-on-services.h','radio-on-multicast.h','radio-on-restore.h','radio-on-disabled.h','precreated-down-client.h','precreated-down-observe.h','cold-on-admission.h','cold-on-generation.h','precreated-down-recovery.h','cold-on-recovery.h','cold-on-main.h','cold-on-guest.h','cold-on-services.h','cold-on-multicast.h','cold-on-owner.h','cold-on-handoff.h','cold-on-release.h','cold-on-policy.h','cold-on-disabled.h','cold-on-disabled-release.h','cold-on-prehandoff.h','cold-on-shutdown.h','cold-on-postshutdown.h','cold-on-root.h','cold-on-root-recovery.h','cold-on-root-signal.h','cold-on-scheduler.h','cold-on-select.h','cold-on-entry.h','radio-entry-result.h','rc-boot.h','rc-normal-shutdown.h','rc-cold-disabled-completion.h','rc-cold-start.h','rc-cold-shutdown.h','rc-cold-completion.h','precreated-down-wire.h','radio-on-rollback-state.h','radio-on-handoff.h','radio-on-release.h','radio-on-followup.h','radio-on-owner.h','radio-on-prehandoff.h','radio-on-shutdown-check.h','radio-on-shutdown.h','radio-on-release-runtime.h','radio-on-aux.h','radio-off-policy.h','radio-off-owner.h','restart-terminal-iapp.h','restart-wan-followup.h','restart-wan-plan.h','restart-iapp-child.h','restart-radio-state.h','restart-auth-stop.h','restart-multicast.h','restart-multicast-policy.h','restart-multicast-controller.h','rc-backend.h','config-backend.h','config-owner.h','saved-config-store.h','saved-config.h','generation-profile.h','native-flash-reader.h','flash-save-attempt.h','flash-worker.h','flash-worker-wire.h','config-save-owner.h','config-save-server.h','native-flash-wire.h','flash-image.h','saved-config-flash.h','rc-quiesce.h','rc-runtime.h','physical-stop-client.h','physical-stop-down.h','physical-stop-session.h','rc-physical-stop.h','physical-rebind-client.h','physical-rebind-controller.h','rebind-start.h','rebind-network.h','rebind-rollback.h','rebind-commit.h','rebind-close.h','rebind-closed-rollback.h','rebind-runner.h','rebind-active-stop.h','rebind-observe.h','rebind-owner.h','initial-restart-select.h','restart-initial-parent.h','restart-initial-handoff.h','restart-profile.h','restart-main-state.h','restart-generation.h','restart-profile-receipt.h','profile-history.h','restart-profile-history.h','restart-main-up.h','restart-main-controller.h','restart-main-bridge.h','restart-guest-up.h','restart-guest-policy.h','restart-guest-bridge.h','restart-guest-isolation.h','restart-guest-controller.h','restart-service-policy.h','restart-services.h','restart-restore.h','restart-resume.h','restart-scheduler.h','physical-rebind-wire.h','physical-stop-response.h','physical-stop-wire.h','physical-initial-wire.h','physical-initial-client.h','physical-initial-session.h','rc-initial-stop.h','initial-shutdown-owner.h','physical-stop-client.h') if root==rc else ())
 headers+=('config-view-channel.h','config-view-endpoint.h','config-view.h','config-view-runtime.h')
 if root==rc:headers+=('config-edit-server.h','config-edit-lease.h','config-edit-pin.h','config-runtime-request.h')
 for name in headers:
  target=root/'wr-iot'/name;data=(local/name).read_bytes()
  if target.exists() and target.read_bytes()!=data:raise SystemExit('Conflicting runtime header: '+str(target))
  pending[target]=data
 for unit in units:
  text=(local/(unit+'.c')).read_text()
  if unit=='rc-backend':text+='\n'+(local/'rc-initial-restart-start.inc').read_text()+(local/'rc-initial-restart-detach.inc').read_text()+(local/'rc-profile-history.inc').read_text()+'\n#include "rc-cold-start.h"\n'+(local/'rc-cold-start.inc').read_text()+''.join((local/name).read_text() for name in ['rc-cold-detach.inc','rc-cold-release.inc','rc-cold-followup.inc','rc-cold-terminal.inc','rc-cold-completion.inc','rc-cold-disabled-release.inc','rc-cold-disabled-followup.inc','rc-cold-disabled-terminal.inc','rc-cold-disabled-completion.inc','rc-cold-prehandoff.inc','rc-cold-shutdown.inc','rc-cold-shutdown-release.inc','rc-cold-final-shutdown.inc','rc-cold-route-handoff.inc','rc-on-disabled-retire.inc','rc-restart-profile-history.inc'])
  for header in local.glob('*.h'):
   text=text.replace('#include "'+header.name+'"','#include "wr-iot/'+header.name+'"')
  target=root/('wr-iot-'+unit+'.c')
  if target.exists():raise SystemExit('Refuse to overwrite runtime source: '+str(target))
  pending[target]=text.encode()
view_route='{ "wr_iot_view.cgi", "application/json", no_cache_IE, wr_iot_http_apply_input, wr_iot_http_view_output, 1 }'
http_view_bound=(http/'web_ex.c').is_file() and (http/'web_ex.c').read_text().count(view_route)==1
http_edit_bound=bool(http_view_bound) and all((http/'web_ex.c').read_text().count('{ "wr_iot_edit_'+suffix+'.cgi", "application/json", no_cache_IE, wr_iot_http_apply_input, wr_iot_http_edit_'+suffix+'_output, 1 }')==1 for suffix in ('ram','auto','save','runtime'))
pending[a.source/'iot-edit-view-source.json']=json.dumps({'board':'WR1200JS','edit_startup_attempt_prepared':True,'view_startup_attempt_prepared':True,'native_capabilities_verified':bool(snapshot['verified'] and flash_readback['verified']),'http_view_bound':bool(http_view_bound),'http_edit_bound':http_edit_bound,'http_runtime_toggle_bound':http_edit_bound,'http_bound':bool(http_view_bound and http_edit_bound),'target_verified':False,'runtime_verified':False,'production_ready':False},indent=2).encode()+b'\n'
for target,data in pending.items():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(a.source/'iot-runtime-source.json').write_text(json.dumps({'board':'WR1200JS','configuration_save_startup_registered':True,'generation_selector_strong_binding_prepared':True,'close_busy_pre_mutation_bound':True,'close_busy_request_opcode':21,'configuration_ram_control_bound':True,'configuration_snapshot_verified':snapshot['verified'],'configuration_snapshot_evidence':snapshot,'configuration_flash_readback_verified':flash_readback['verified'],'configuration_flash_readback_evidence':flash_readback,'configuration_flash_bound':False,'configuration_loaded_promotion_bound':False,'activation_backend_installed':True,'http_private_status_backend_installed':True,'pid1_wait_bound':True,'status_peer_pid':1,'status_peer_uid':0,'progress_period_ms':100,'initial_off_admission':True,'off_reopen_admission':True,'physical_stop_transport_linked':True,'physical_stop_private_quiesce_linked':True,'physical_stop_wait_continuation_bound':True,'physical_stop_rc_entrypoints_bound':False,'rebind_network_helpers_linked':True,'rebind_close_helpers_linked':True,'rebind_runner_linked':True,'rebind_active_off_observer_linked':True,'rebind_backend_routing_linked':True,'rebind_off_reopen_handoff':True,'rebind_repeat_admission':True,'restart_profile_observer_linked':True,'restart_generation_linked':True,'restart_main_controller_linked':True,'restart_main_bridge_linked':True,'restart_resume_progress_bound':True,'restart_resume_begin_bound':True,'restart_resume_linked':True,'restart_resume_bound':False,'restart_restore_linked':True,'restart_restore_bound':False,'restart_services_linked':True,'restart_services_bound':False,'restart_guest_controller_linked':True,'restart_guest_controller_bound':False,'restart_guest_up_linked':True,'restart_guest_down_preparation_linked':True,'physical_stop_restart_resume_bound':False,'physical_stop_rc_orchestration':False,'radio_on_root_progress_bound':True,'radio_on_followup_linked':True,'radio_on_disabled_backend_handoff_linked':True,'completed_profile_history_linked':True,'restart_finish_profile_history_linked':True,'radio_off_frozen_profile_history_linked':True,'radio_on_parent_release_linked':True,'radio_on_handoff_linked':True,'radio_on_restore_linked':True,'radio_on_aux_observer_linked':True,'radio_on_multicast_linked':True,'radio_on_guest_linked':True,'radio_on_services_linked':True,'radio_on_generation_linked':True,'radio_on_main_linked':True,'radio_on_admission_linked':True,'cold_on_admission_linked':True,'cold_on_generation_linked':True,'cold_on_main_linked':True,'cold_on_preup_recovery_linked':True,'cold_on_entry_bound':False,'cold_backend_initial_start_linked':True,'cold_completion_private_api_linked':True,'cold_disabled_completion_private_api_linked':True,'cold_completion_public_entry_bound':False,'radio_on_entry_bound':False,'radio_off_consumer_linked':True,'radio_off_entry_bound':False,'radio_off_progress_bound':True,'radio_off_profile_ram_progress_bound':True,'normal_shutdown_controller_linked':True,'normal_shutdown_dispatch_bound':True,'normal_shutdown_notification_bound':True,'normal_shutdown_route_armed':False,'normal_shutdown_initial_active_arm_bound':True,'normal_shutdown_cold_active_arm_bound':True,'normal_shutdown_cold_routed_handoff_bound':True,'normal_shutdown_mailbox_active_arm_bound':True,'production_ready':False,'runtime_verified':False},indent=2)+'\n')
print('PASS experimental WR runtime/backend/status sources staged; initial OFF and CLOSED-witness reopen staged; production acceptance unresolved')
