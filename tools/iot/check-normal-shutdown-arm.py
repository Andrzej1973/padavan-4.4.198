from pathlib import Path
import tempfile,subprocess
here=Path(__file__).resolve().parent
source=(here/'check-rc-normal-shutdown.py').read_text()
ns={'__file__':str(here/'check-rc-normal-shutdown.py')}
exec(compile(source[:source.index('\nfailure=')],'<normal controller fixture>','exec'),ns)
code=ns['code'].split('int main(void){',1)[0]
code+=r'''
static void ready_signal(int sig){if(!wr_iot_rc_shutdown_note(sig))shutdowns++;}
int main(void){
 (void)handler;(void)notification_test_signal;
 assert(!wr_iot_rc_normal_shutdown_arm_ready()&&!wr_iot_rc_shutdown.normal_route_armed);
 wr_iot_rc_shutdown.active=1;
 assert(wr_iot_rc_normal_shutdown_arm_ready());
 assert(wr_iot_rc_normal_shutdown_terminal_arm_ready());
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_rc_normal_shutdown_terminal_arm_ready()&&!wr_iot_rc_normal_shutdown_arm_ready());
 assert(!wr_iot_rc_shutdown_begin()); /* terminal transfer grants no new ON */
 wr_iot_rc_shutdown.pending=SIGQUIT;assert(wr_iot_rc_normal_shutdown_terminal_arm_ready());
 wr_iot_rc_shutdown.pending=SIGPWR;assert(!wr_iot_rc_normal_shutdown_terminal_arm_ready());
 wr_iot_rc_shutdown.pending=0;normal_shutdown.spent=1;
 assert(!wr_iot_rc_normal_shutdown_terminal_arm_ready());normal_shutdown.spent=0;
 wr_iot_rc_shutdown.active=2;assert(!wr_iot_rc_normal_shutdown_terminal_arm_ready());
 wr_iot_rc_shutdown.active=1;

 assert(!wr_iot_rc_normal_shutdown_cold_arm_ready());
 wr_iot_rc_shutdown.radio_off_owned=1;
 assert(wr_iot_rc_normal_shutdown_cold_arm_ready()&&!wr_iot_rc_normal_shutdown_arm_ready());
 wr_iot_rc_shutdown.radio_off_owned=2;assert(!wr_iot_rc_normal_shutdown_cold_arm_ready());
 wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.radio_on_owned=1;
 assert(!wr_iot_rc_normal_shutdown_cold_arm_ready());
 wr_iot_rc_shutdown.radio_on_owned=0;normal_shutdown.spent=1;
 assert(!wr_iot_rc_normal_shutdown_cold_arm_ready());normal_shutdown.spent=0;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_rc_normal_shutdown_cold_arm_ready());
 wr_iot_rc_shutdown.pending=0;wr_iot_rc_shutdown.radio_off_owned=0;
 notification_owner=getpid();assert(wr_iot_rc_normal_shutdown_arm_ready());
 assert(notification_owner==getpid());notification_owner=0;
#define REFUSE(field,value) do{field=value;assert(!wr_iot_rc_normal_shutdown_arm_ready());field=0;}while(0)
 REFUSE(normal_shutdown.owner,getpid());REFUSE(normal_shutdown.generated,1);
 REFUSE(normal_shutdown.claimed,1);REFUSE(normal_shutdown.retained,1);REFUSE(normal_shutdown.spent,1);
 REFUSE(wr_iot_rc_shutdown.pending,SIGTERM);REFUSE(wr_iot_rc_shutdown.normal_route_requested,SIGQUIT);
 REFUSE(wr_iot_rc_shutdown.replay_signal,SIGTERM);
 REFUSE(wr_iot_rc_shutdown.radio_on_owned,1);REFUSE(wr_iot_rc_shutdown.radio_off_owned,1);
#undef REFUSE
 struct sigaction sa={0};sa.sa_handler=ready_signal;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,0));
 assert(wr_iot_rc_normal_shutdown_arm_ready());
 /* Signal after preflight: commit cannot reject and lose this request. */
 assert(!raise(SIGTERM)&&wr_iot_rc_shutdown.pending==SIGTERM&&!shutdowns);
 wr_iot_rc_normal_shutdown_arm_commit();
 assert(wr_iot_rc_shutdown.normal_route_armed&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(wr_iot_rc_shutdown_end()==SIGTERM&&!raise(SIGTERM));
 assert(!shutdowns&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());
 wr_iot_rc_shutdown.radio_on_owned=1;
 assert(wr_iot_rc_normal_shutdown_cold_handoff_ready());
 notification_owner=getpid();assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());notification_owner=0;
 normal_shutdown.spent=1;assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());normal_shutdown.spent=0;
 wr_iot_rc_shutdown.radio_on_owned=2;assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());
 wr_iot_rc_shutdown.radio_on_owned=1;wr_iot_rc_shutdown.radio_off_owned=1;
 assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());wr_iot_rc_shutdown.radio_off_owned=0;
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());wr_iot_rc_shutdown.active=0;
 wr_iot_rc_shutdown.normal_route_requested=SIGPWR;assert(!wr_iot_rc_normal_shutdown_cold_handoff_ready());

}
'''
with tempfile.TemporaryDirectory(prefix='wr-arm-ready-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual normal-controller readiness: unavailable/owned/generated/claimed/retained/spent/pending/replay/exclusion refusals; notification preserved; post-preflight TERM committed to route, no stock signal. INITIAL integration not yet tested')
