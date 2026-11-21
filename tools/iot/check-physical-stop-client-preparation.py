"""Actual runtime preparer links isolated client objects without RC activation."""
from pathlib import Path
import ast,json,subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-stop-client-prepared-') as d:
 root=Path(d);rc=root/'trunk/user/rc';http=root/'trunk/user/httpd'
 for role in (rc,http):(role/'wr-iot').mkdir(parents=True)
 (root/'iot-control-source.json').write_text(json.dumps({'board':'WR1200JS'}))
 (rc/'wr-iot/activation-owner.h').write_text('/* prerequisite marker only */')
 (rc/'init.c').write_text('#include "wr-iot/rc-shutdown-admission.h"\n\tinit_router();\n\t\twhile ( !sig_usr1_received &&\n\t\t\t!sig_alrm_received ) {\n\t\t\t\tsigsuspend(&ss);\n}\n')
 (rc/'init.c').write_text((rc/'init.c').read_text()+'''\t\tif (sig_usr1_received) {
\t\t\tsig_usr1_received = 0;
\t\t\thandle_notifications();
\t\t}
\t\tif (sig_alrm_received) {
\t\t\tsig_alrm_received = 0;
#if defined (USE_USB_SUPPORT) || defined (USE_STORAGE)
\t\t\ton_deferred_hotplug_dev();
#endif
\t\t}
''')
 (rc/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 (rc/'Makefile').write_text('OBJS += wr-iot-control-mailbox.o wr-iot-control-server.o\n')
 producer=ast.parse((here/'prepare-rc.py').read_text())
 selector=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id=='include' for t in n.targets))
 (rc/'ralink.c').write_text(selector)
 (http/'Makefile').write_text('OBJS += wr-iot-control-mailbox.o wr-iot-control-client.o\n')
 for header in ('driver-api-wire.h','radio-stop-fence.h','rc-shutdown-admission.h','service-guard.h','rc-backend.h','control-record.h','request.h','types.h','subnet.h','driver-api-client.h','driver-api-open-current-wire.h','driver-api-open-recovery-wire.h','driver-api-close-wire.h','driver-api-close-progress-wire.h','driver-api-close-release-wire.h','precreated-idle-wire.h'):
  (rc/'wr-iot'/header).write_bytes((here/header).read_bytes())
 for header in here.glob('*.h'):
  if header.name!='activation-owner.h':(rc/'wr-iot'/header.name).write_bytes(header.read_bytes())
 (rc/'shared-wifi').mkdir()
 (rc/'shared-wifi/validate.h').write_bytes((here.parent/'shared-wifi/validate.h').read_bytes())
 # These headers must be staged by runtime, not accidentally supplied by
 # the fixture's broad baseline prerequisite collection.
 for name in ('cold-on-scheduler.h','cold-on-select.h','cold-on-entry.h','radio-entry-result.h'):
  (rc/'wr-iot'/name).unlink()
 subprocess.run(['python3',str(here/'prepare-runtime.py'),str(root)],check=True)
 manifest=json.loads((root/'iot-runtime-source.json').read_text())
 assert manifest['generation_selector_strong_binding_prepared'] is True
 assert '__attribute__((weak)) int wr_iot_generation_profile_request' not in (rc/'ralink.c').read_text()
 init=(rc/'init.c').read_text();assert init.count('wr_iot_rc_boot_arm();')==1 and init.index('init_router();')<init.index('wr_iot_rc_boot_arm();')
 start=init.index('\tinit_router();');end=init.index('#endif',init.index('wr_iot_rc_boot_arm();',start))+len('#endif')
 startup=init[start:end]
 probe='#include <assert.h>\nstatic int stage;\nvoid init_router(void){stage=1;}\nint wr_iot_rc_save_backend_install(void){assert(stage==1);stage=2;return 0;}\nint wr_iot_rc_edit_backend_install(void){assert(stage==2);stage=3;return 0;}\nint wr_iot_rc_view_runtime_install(void){assert(stage==3);stage=4;return 0;}\nvoid wr_iot_rc_boot_arm(void){assert(stage==4);stage=5;}\nint main(void){\n'+startup+'\n#if defined(BOARD_WR1200JS) && WR_IOT_IAPP_POLICY_PREPARED\nassert(stage==5);\n#elif defined(BOARD_WR1200JS)\nassert(stage==4);\n#else\nassert(stage==1);\n#endif\nreturn 0;}\n'
 boot_probe=root/'boot-hook.c';boot_probe.write_text(probe)
 for board in ('WR1200JS','OTHER'):
  for gate in ('0','1'):
   binary=root/('boot-hook-'+board+gate)
   subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-DBOARD_'+board,'-DWR_IOT_IAPP_POLICY_PREPARED='+gate,str(boot_probe),'-o',str(binary)],check=True)
   subprocess.run([str(binary)],check=True,timeout=5)

 loop_start=init.index('#if defined(BOARD_WR1200JS)\n\t\twhile ')
 loop_end=init.index('\n}\n',loop_start)+3
 loop=init[loop_start:loop_end]
 loop_probe=r'''#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <signal.h>
int routed=1,waits,legacy;
int wr_iot_rc_normal_shutdown_pending(void){return routed;}
void wr_iot_rc_wait(const sigset_t *m,const volatile int *n,const volatile int *a){
 assert(m&&*n==1&&*a==1);waits++;routed=0;
}
int fixture_suspend(const sigset_t *m){assert(m);legacy++;return 0;}
#define sigsuspend fixture_suspend
int main(void){
 int sig_usr1_received=1,sig_alrm_received=1;sigset_t ss;sigemptyset(&ss);
'''+loop+r'''
#if defined(BOARD_WR1200JS)
 assert(waits==1&&!legacy&&!routed);
#else
 assert(!waits&&!legacy&&routed);
#endif
 assert(sig_usr1_received==1&&sig_alrm_received==1);(void)ss;return 0;
}
'''
 loop_file=root/'shutdown-wait-hook.c';loop_file.write_text(loop_probe)
 for board in ('WR1200JS','OTHER'):
  binary=root/('shutdown-wait-hook-'+board)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-DBOARD_'+board,str(loop_file),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=5)
 notification_probe=r'''#include <assert.h>
int sig_usr1_received=1,sig_alrm_received=1,routed=1,actions,ends;
int wr_iot_rc_normal_notification_begin(void){return !routed;}
void wr_iot_rc_normal_notification_end(void){ends++;}
void handle_notifications(void){actions++;routed=1;}
void on_deferred_hotplug_dev(void){actions++;}
void dispatch(void){
'''+init[loop_end:]+r'''
}
int main(void){
 dispatch();
#if defined(BOARD_WR1200JS)
 assert(sig_usr1_received==1&&sig_alrm_received==1&&!actions&&!ends);
 routed=0;dispatch();
 assert(!sig_usr1_received&&sig_alrm_received==1&&actions==1&&ends==1);
#else
 assert(!sig_usr1_received&&!sig_alrm_received&&actions==2&&!ends);
#endif
 return 0;
}
'''
 notify_file=root/'shutdown-notification-hook.c';notify_file.write_text(notification_probe)
 for board in ('WR1200JS','OTHER'):
  binary=root/('shutdown-notification-hook-'+board)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-DUSE_USB_SUPPORT','-DBOARD_'+board,str(notify_file),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=5)
 assert manifest['normal_shutdown_notification_bound']
 assert manifest['normal_shutdown_controller_linked'] and manifest['normal_shutdown_dispatch_bound']
 assert not manifest['normal_shutdown_route_armed']
 assert manifest['radio_on_root_progress_bound'] and not manifest['radio_on_entry_bound']
 assert manifest['radio_on_followup_linked']
 assert manifest['radio_on_parent_release_linked']
 assert manifest['radio_on_handoff_linked']
 assert manifest['radio_on_restore_linked'] and manifest['radio_on_aux_observer_linked'] and manifest['radio_on_multicast_linked']
 assert manifest['radio_on_guest_linked'] and manifest['radio_on_services_linked']
 assert manifest['radio_on_generation_linked'] and manifest['radio_on_main_linked']
 assert manifest['cold_on_admission_linked'] and manifest['cold_on_generation_linked']
 assert manifest['cold_disabled_completion_private_api_linked']
 assert manifest['cold_completion_private_api_linked'] and not manifest['cold_completion_public_entry_bound']
 assert manifest['cold_backend_initial_start_linked']
 assert (rc/'wr-iot-rc-backend.c').read_text().count('int wr_iot_rc_cold_start_begin(')==1
 for symbol in ['wr_iot_rc_cold_start_begin','wr_iot_rc_cold_active_current','wr_iot_rc_cold_start_progress','wr_iot_rc_cold_parent_release','wr_iot_rc_cold_terminal_begin','wr_iot_rc_cold_terminal_step','wr_iot_rc_cold_terminal_retire','wr_iot_rc_cold_shutdown_closed','wr_iot_rc_cold_shutdown_rejected','wr_iot_rc_cold_shutdown_advance','wr_iot_rc_cold_shutdown_off_begin','wr_iot_rc_cold_postshutdown_release','wr_iot_rc_cold_root_final_shutdown','wr_iot_rc_cold_disabled_parent_release','wr_iot_rc_cold_disabled_terminal_begin','wr_iot_rc_cold_disabled_terminal_step','wr_iot_rc_cold_disabled_terminal_retire']:
  assert ('rc-backend:'+symbol) in (here/'compile-runtime-link.sh').read_text()
 assert manifest['cold_on_main_linked'] and manifest['cold_on_preup_recovery_linked'] and not manifest['cold_on_entry_bound']
 assert manifest['radio_on_admission_linked'] and not manifest['radio_on_entry_bound']
 assert manifest['radio_off_consumer_linked'] and not manifest['radio_off_entry_bound']
 assert manifest['physical_stop_private_quiesce_linked']
 assert manifest['physical_stop_transport_linked'] and not manifest['physical_stop_rc_orchestration']
 assert manifest['physical_stop_wait_continuation_bound'] and not manifest['physical_stop_rc_entrypoints_bound']
 assert manifest['restart_guest_down_preparation_linked']
 assert manifest['restart_resume_progress_bound'] and manifest['restart_resume_begin_bound']
 assert manifest['restart_resume_linked'] and not manifest['restart_resume_bound']
 assert manifest['restart_restore_linked'] and not manifest['restart_restore_bound']
 assert manifest['restart_services_linked'] and not manifest['restart_services_bound']
 assert manifest['restart_guest_controller_linked'] and not manifest['restart_guest_controller_bound']
 assert manifest['restart_guest_up_linked']
 assert manifest['restart_main_bridge_linked']
 assert manifest['restart_main_controller_linked']
 assert manifest['restart_generation_linked']
 assert manifest['restart_profile_observer_linked']
 assert manifest['rebind_repeat_admission']
 assert manifest['rebind_backend_routing_linked'] and manifest['rebind_off_reopen_handoff']
 assert manifest['rebind_active_off_observer_linked']
 assert manifest['rebind_close_helpers_linked'] and manifest['rebind_runner_linked']
 assert not manifest['physical_stop_restart_resume_bound'] and manifest['rebind_network_helpers_linked']
 (rc/'wr-iot/activation-owner.h').write_bytes((here/'activation-owner.h').read_bytes())
 for name in ('initial-restart-select','restart-initial-parent','restart-initial-handoff','rc-backend','physical-stop-client','physical-stop-down','physical-stop-session','rc-physical-stop','physical-rebind-client','physical-rebind-controller','rebind-start','rebind-network','rebind-rollback','rebind-commit','rebind-close','rebind-closed-rollback','rebind-runner','rebind-active-stop','rebind-observe','rebind-owner','restart-profile','restart-main-state','restart-generation','restart-main-up','restart-main-controller','restart-main-bridge','restart-guest-up','restart-guest-bridge','restart-guest-isolation','restart-guest-controller','restart-services','restart-restore','restart-finish-check','restart-resume','restart-cancel-check','restart-prehandoff-check','restart-resume-retire','restart-scheduler','restart-auth-stop','restart-multicast','restart-multicast-controller','restart-iapp-child','restart-wan-followup','restart-terminal-iapp','radio-off-owner','radio-off-observe','radio-on-admission','radio-on-generation','radio-on-main','radio-on-guest','radio-on-services','radio-on-multicast','radio-on-restore','radio-on-disabled','precreated-down-client','precreated-down-observe','cold-on-admission','cold-on-generation','precreated-down-recovery','cold-on-recovery','cold-on-main','cold-on-guest','cold-on-services','cold-on-multicast','cold-on-owner','cold-on-handoff','cold-on-release','cold-on-policy','cold-on-disabled','cold-on-disabled-release','cold-on-prehandoff','cold-on-shutdown','cold-on-postshutdown','cold-on-root','cold-on-root-shutdown','cold-on-root-recovery','cold-on-root-signal','cold-on-scheduler','cold-on-select','cold-on-entry','rc-boot','radio-on-handoff','radio-on-release','radio-on-followup','radio-on-owner','radio-on-prehandoff','radio-on-shutdown-check','radio-on-shutdown','radio-on-aux','radio-off-profile','radio-off-profile-check','radio-off-followup','radio-off-bridge','radio-off-wan'):
  assert (rc/'Makefile').read_text().count('wr-iot-'+name+'.o')==1
  subprocess.run(['gcc','-std=gnu11' if name=='rc-backend' else '-std=c11','-Wall','-Wextra','-Werror','-O2','-I'+str(rc),'-c',str(rc/('wr-iot-'+name+'.c')),'-o',str(root/(name+'.o'))],check=True)
 staged_api=root/'initial-saved-api.c';staged_api.write_text('#include "wr-iot/rc-physical-stop.h"\nint (*saved_initial_entry)(const struct wr_iot_rc_physical_intent *)=wr_iot_rc_physical_begin_initial_saved;\n')
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(rc),'-c',str(staged_api),'-o',str(root/'initial-saved-api.o')],check=True)
 physical_symbols=subprocess.check_output(['nm',str(root/'rc-physical-stop.o')],text=True)
 assert any(line.split()[-2:]==['T','wr_iot_rc_physical_begin_initial_saved'] for line in physical_symbols.splitlines())
 symbols=subprocess.check_output(['nm',str(root/'rc-backend.o')],text=True)
 for symbol in ['wr_iot_rc_cold_parent_release','wr_iot_rc_cold_terminal_begin','wr_iot_rc_cold_terminal_step','wr_iot_rc_cold_terminal_retire','wr_iot_rc_cold_shutdown_closed','wr_iot_rc_cold_shutdown_rejected','wr_iot_rc_cold_shutdown_advance','wr_iot_rc_cold_shutdown_off_begin','wr_iot_rc_cold_postshutdown_release','wr_iot_rc_cold_root_final_shutdown','wr_iot_rc_cold_disabled_parent_release','wr_iot_rc_cold_disabled_terminal_begin','wr_iot_rc_cold_disabled_terminal_step','wr_iot_rc_cold_disabled_terminal_retire']:
  assert any(line.split()[-2:]==['T',symbol] for line in symbols.splitlines()),symbol
 # Execute the actual verifier's source-equality loop against prepared units,
 # including the composed private backend. Deliberate corruption must refuse.
 verifier=ast.parse((here/'check-runtime-source.py').read_text())
 outer=next(n for n in verifier.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple))
 source_check=next(node for node in outer.body if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='u')
 code=compile(ast.Module(body=[source_check],type_ignores=[]),'<actual-runtime-source-check>','exec')
 env={'local':here,'root':rc,'units':['rc-backend','cold-on-release','cold-on-policy','cold-on-disabled','cold-on-disabled-release','cold-on-prehandoff','cold-on-shutdown','cold-on-postshutdown','cold-on-root','cold-on-root-shutdown','cold-on-root-recovery','cold-on-root-signal','cold-on-scheduler','cold-on-select','cold-on-entry','rc-boot']}
 exec(code,env)
 backend_path=rc/'wr-iot-rc-backend.c';original=backend_path.read_text()
 backend_path.write_text(original+'/* unexpected source */')
 try:
  exec(code,env)
 except AssertionError:
  pass
 else:
  raise AssertionError('runtime source verifier accepted backend corruption')
 backend_path.write_text(original)
 duplicate=subprocess.run(['python3',str(here/'prepare-runtime.py'),str(root)],capture_output=True)
 assert duplicate.returncode!=0
print('PASS actual runtime preparation: fixed client/DOWN objects copied and compile, exact Makefile entries, no orchestration flag, duplicate refused; full SDK/MIPS separate')
