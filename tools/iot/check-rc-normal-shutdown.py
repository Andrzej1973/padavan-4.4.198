"""Actual PID1 shutdown controller with actual physical/session/fence; IO actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
code=code.replace('int wr_iot_rc_normal_shutdown_arm_ready(void){assert(0);return 0;}','')
code=code.replace('#include "rc-shutdown-admission.h"',r'''static int replay_raise_failures;
static int controlled_replay_raise(int);
#define raise controlled_replay_raise
#include "rc-shutdown-admission.h"
#undef raise
static int controlled_replay_raise(int sig){
 if(replay_raise_failures){replay_raise_failures--;return -1;}
 return raise(sig);
}
''',1)
code+=r'''
static int time_unavailable;
static int normal_clock(clockid_t clock,struct timespec *out){
 assert(clock==CLOCK_MONOTONIC);if(time_unavailable)return -1;
 out->tv_sec=23;out->tv_nsec=0;return 0;
}
#include <syslog.h>
static unsigned int shutdown_reports;
static void capture_shutdown_log(int priority,const char *message,...){
 if(priority==LOG_NOTICE){assert(strstr(message,"RC shutdown deferred"));return;}
 assert(priority==LOG_ERR);
 assert(!strcmp(message,"MT7603 RC shutdown retained: physical radio OFF failed"));
 shutdown_reports++;
}
#define syslog capture_shutdown_log
#define clock_gettime normal_clock
#include "rc-normal-shutdown.c"
#undef clock_gettime
#undef syslog
static void notification_test_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!normal_shutdown.owner&&normal_shutdown.spent);
 assert(!normal_shutdown.off.id[0]&&!wr_iot_rc_shutdown.normal_route_armed);
 shutdowns++;
}
int main(void){
 (void)handler;
 struct sigaction sa={0};sa.sa_handler=notification_test_signal;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,NULL));
 assert(!wr_iot_rc_normal_shutdown_pending()&&!wr_iot_rc_normal_shutdown_step());
 assert(wr_iot_rc_normal_notification_begin());wr_iot_rc_normal_notification_end();
 assert(wr_iot_rc_shutdown_route_arm());
 assert(wr_iot_rc_normal_notification_begin()&&notification_owner==getpid());
 assert(!wr_iot_rc_normal_notification_begin());
 sigset_t before,after;assert(!sigprocmask(SIG_SETMASK,NULL,&before));
 assert(!raise(SIGTERM));
 assert(!wr_iot_rc_normal_shutdown_step()&&!physical.owner); /* admitted batch drains first */
 assert(!sigprocmask(SIG_SETMASK,NULL,&after));
 assert(sigismember(&before,SIGTERM)==sigismember(&after,SIGTERM));
 wr_iot_rc_normal_notification_end();
 assert(!wr_iot_rc_normal_notification_begin());
 assert(wr_iot_rc_normal_shutdown_pending());
 wr_iot_rc_shutdown.radio_on_owned=1;
 assert(!wr_iot_rc_normal_shutdown_step()&&!normal_shutdown.generated&&!physical.owner);
 wr_iot_rc_shutdown.radio_on_owned=0;
 time_unavailable=1;assert(!wr_iot_rc_normal_shutdown_step()&&!normal_shutdown.generated);
 time_unavailable=0;entropy_fail=1;
 assert(!wr_iot_rc_normal_shutdown_step()&&!normal_shutdown.generated&&!physical.owner);
 entropy_fail=0;assert(!wr_iot_rc_normal_shutdown_step());
 assert(normal_shutdown.claimed&&normal_shutdown.off.created==23&&physical.routed_shutdown);
 char id[33];memcpy(id,normal_shutdown.off.id,sizeof(id));
 assert(wr_iot_control_id(id)&&!normal_shutdown.off.request.enabled);
 for(int i=0;i<20&&!downs;i++)assert(!wr_iot_rc_normal_shutdown_step());
 assert(downs==1&&normal_shutdown.claimed&&!shutdowns);
 assert(!strcmp(id,normal_shutdown.off.id));
 query_status=WR_STOP_COMPLETE;
 replay_raise_failures=100;
 for(int i=0;i<12&&!normal_shutdown.spent;i++)(void)wr_iot_rc_normal_shutdown_step();
 assert(!shutdowns&&normal_shutdown.spent&&!normal_shutdown.owner&&!physical.owner);
 assert(wr_iot_rc_normal_shutdown_pending()&&wr_iot_rc_shutdown_replay_pending());
 assert(!wr_iot_rc_normal_notification_begin());
 assert(!wr_iot_rc_normal_shutdown_step()&&downs==1);
 replay_raise_failures=0;assert(wr_iot_rc_normal_shutdown_step());
 assert(shutdowns==1&&normal_shutdown.spent&&!normal_shutdown.owner&&!physical.owner);
 assert(!wr_iot_rc_normal_shutdown_pending()&&!wr_iot_rc_normal_shutdown_step());
 assert(downs==1&&aux_calls==6);
}
'''
failure=code[:code.index(' entropy_fail=0;assert(!wr_iot_rc_normal_shutdown_step());')]+r'''
 entropy_fail=0;guard_fail=1;
 assert(!wr_iot_rc_normal_shutdown_step()&&normal_shutdown.claimed&&physical.finishing==-1);
 guard_fail=0;
 assert(!wr_iot_rc_normal_shutdown_step()&&!wr_iot_rc_shutdown.active&&!physical.fence.owner);
 assert(!wr_iot_rc_normal_shutdown_step()&&normal_shutdown.retained&&shutdown_reports==1);
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&!shutdowns&&!calls&&!downs&&!depth);
 assert(!wr_iot_rc_normal_shutdown_step()&&normal_shutdown.retained&&shutdown_reports==1);
}
'''
pending_transaction=code[:code.index(' assert(wr_iot_rc_shutdown_route_arm());')]+r'''
 assert(wr_iot_rc_shutdown_route_arm());
 wr_iot_rc_shutdown.active=1;
 assert(wr_iot_rc_shutdown_note(SIGTERM));
 assert(!wr_iot_rc_shutdown.normal_route_requested&&wr_iot_rc_shutdown.pending==SIGTERM);
 assert(wr_iot_rc_normal_shutdown_pending());
 assert(!wr_iot_rc_normal_notification_begin()&&!notification_owner);
 assert(!wr_iot_rc_normal_shutdown_step()&&!physical.owner);
 assert(wr_iot_rc_shutdown_end()==SIGTERM);
 assert(!raise(SIGTERM)&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 assert(!wr_iot_rc_normal_notification_begin());
}
'''
for variant,test in (('success',code),('preparation-refused',failure),('pending-transaction',pending_transaction)):
 with tempfile.TemporaryDirectory(prefix='wr-rc-normal-shutdown-'+variant+'-') as d:
  p=Path(d)/'check.c';p.write_text(test);b=Path(d)/'check'
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=15)
print('PASS PID1 normal shutdown controller: no automatic arm, existing owner/time/entropy refusal, one stable OFF, bounded physical progression, private controller retired before stock replay, spent prevents replay; backend/IO actors, no runtime binding')
