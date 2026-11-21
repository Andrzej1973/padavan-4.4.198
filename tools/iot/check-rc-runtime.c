#define _GNU_SOURCE
#include <assert.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ADMISSION
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
#endif
static char directory[]="/tmp/iot-rc-runtime-XXXXXX";
#define WR_IOT_CONTROL_DIRECTORY directory
#define WR_IOT_RUNTIME_UID geteuid()
#include "rc-runtime.c"
static int save_observations,save_verdict;
static int edit_observations,edit_verdict;
int wr_iot_rc_edit_observed(const struct wr_iot_control_result *r)
{assert(r->state==WR_IOT_RESULT_STORED_RAM||r->state==WR_IOT_RESULT_SAVED_FLASH||r->state==WR_IOT_RESULT_APPLIED);edit_observations++;return edit_verdict;}
int wr_iot_rc_save_observed(const struct wr_iot_control_result *r)
{assert(r->state==WR_IOT_RESULT_STORED_RAM||r->state==WR_IOT_RESULT_SAVED_FLASH);save_observations++;return save_verdict;}

#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ON_RELEASE
int wr_iot_on_shutdown_closed_current(struct wr_iot_on_restore*s,const struct wr_iot_rc_quiesce*o){(void)s;(void)o;assert(0);return 0;}
int wr_iot_on_prehandoff_cancel_current(struct wr_iot_on_restore*s){(void)s;assert(0);return 0;}
int wr_iot_on_release_current(struct wr_iot_on_restore *s){(void)s;assert(0);return 0;}
int wr_iot_wan_followup_capture(struct wr_iot_wan_followup_state *s,int on){(void)s;(void)on;assert(0);return 0;}
int wr_iot_radio_stop_fence_end_cleanup(struct wr_iot_radio_stop_fence *s,void(*cleanup)(void*),void*c){(void)s;(void)cleanup;(void)c;assert(0);return 0;}
int wr_iot_service_guard_dup(void){assert(0);return -1;}
void wr_iot_service_guard_leave(int token){(void)token;assert(0);}
#endif
#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_ON_OWNER
int wr_iot_radio_on_pending(void){return 0;}
int wr_iot_radio_on_step(void){assert(0);return 0;}
int wr_iot_radio_on_retire(void){assert(0);return 0;}
#endif
#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_COLD_OWNER
int wr_iot_cold_on_pending(void){return 0;}
int wr_iot_cold_on_step(void){assert(0);return 0;}
int wr_iot_cold_on_retire(void){assert(0);return 0;}
#endif
#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_BOOT
int wr_iot_rc_boot_pending(void){return 0;}
int wr_iot_rc_boot_step(void){assert(0);return 0;}
#endif
#ifndef WR_IOT_RUNTIME_FIXTURE_EXTERNAL_NORMAL_SHUTDOWN
static int normal_pending,normal_steps;
int wr_iot_rc_normal_shutdown_pending(void){return normal_pending;}
int wr_iot_rc_normal_shutdown_step(void){normal_steps++;return 0;}
#endif
static volatile int notification,alarm_flag;
static int pending,steps,observations,physical_pending,physical_steps,resume_pending,resume_steps;
int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner*s,const struct wr_iot_control_request*r){(void)s;(void)r;return 0;}
int wr_iot_radio_off_step(struct wr_iot_radio_off_owner*s,int reload){(void)s;(void)reload;assert(0);return 0;}
int wr_iot_off_followup_begin(struct wr_iot_off_followup*s,const struct wr_iot_radio_off_owner*o){(void)s;(void)o;assert(0);return 0;}
enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup*s){(void)s;assert(0);return WR_OFF_FOLLOWUP_IDLE;}
int wr_iot_off_followup_finish(struct wr_iot_off_followup*s,struct wr_iot_radio_off_owner*o){(void)s;(void)o;assert(0);return 0;}
int wr_iot_rc_dispatch(void){assert(0);return 0;}
int wr_iot_restart_scheduler_pending(void){return resume_pending;}
int wr_iot_restart_scheduler_step(void){resume_steps++;return 0;}
int wr_iot_restart_scheduler_retire(void){assert(0);return 0;}
int wr_iot_rc_physical_pending(void){return physical_pending;}
void wr_iot_rc_physical_step(void){physical_steps++;}
int wr_iot_rc_pending(void){return pending;}
int wr_iot_rc_continue(void){steps++;return 1;}
int wr_iot_rc_backend_observed(const struct wr_iot_control_result *r){assert(r->state==WR_IOT_RESULT_APPLIED);observations++;return 1;}
static void handler(int sig){assert(sig==SIGUSR1);notification=1;}
int main(void){
 {
 struct wr_iot_control_result r={.state=WR_IOT_RESULT_SAVED_FLASH};
 assert(!runtime_observed(&r)&&save_observations==1&&edit_observations==1);save_verdict=1;
 assert(runtime_observed(&r)&&save_observations==2);r.state=WR_IOT_RESULT_STORED_RAM;
 assert(runtime_observed(&r)&&save_observations==3);save_verdict=0;
 edit_verdict=1;assert(runtime_observed(&r)&&save_observations==3&&edit_observations==4);edit_verdict=0;
 r.state=WR_IOT_RESULT_APPLIED;edit_verdict=1;
 assert(runtime_observed(&r)&&edit_observations==5&&save_observations==3);edit_verdict=0;
 }
 assert(mkdtemp(directory));sigset_t empty,blocked,old,check;
 sigemptyset(&empty);sigemptyset(&blocked);sigaddset(&blocked,SIGUSR1);
 struct sigaction action={0};action.sa_handler=handler;sigemptyset(&action.sa_mask);assert(!sigaction(SIGUSR1,&action,NULL));
 notification=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(!initialized&&!steps);notification=0;
 /* Unsafe directory first, then repair it: no endpoint replacement or
  * tight retry loop, and recovery after the monotonic retry interval. */
 assert(!chmod(directory,0755));runtime_init();
 assert(initialized&&!listening&&endpoint.listener<0&&next_init);
 unsigned long long retry_due=next_init;
 assert(!chmod(directory,0700));runtime_init();
 assert(!listening&&next_init==retry_due);
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(runtime_ms()>=retry_due&&!listening&&!steps);
 runtime_init();assert(listening&&endpoint.listener>=0);
 pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(initialized&&steps==1&&endpoint.listener>=0);
 unsigned long long due=next_progress;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(steps==2&&runtime_ms()>=due);pending=0;
 physical_pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(physical_steps==1&&steps==2);physical_pending=0;
 resume_pending=pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(resume_steps==1&&steps==2);
 physical_pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(physical_steps==2&&resume_steps==1&&steps==2);physical_pending=0;
 unsigned long long resume_due=next_progress;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(resume_steps==2&&steps==2&&runtime_ms()>=resume_due);resume_pending=pending=0;
 normal_pending=1;notification=1;
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(normal_steps==1&&notification==1&&steps==2);
 pending=1;wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(steps==3&&normal_steps==1);pending=0;steps=2;
 normal_pending=0;notification=0;
 assert(!sigprocmask(SIG_BLOCK,&blocked,&old));pid_t child=fork();assert(child>=0);
 if(!child){assert(!kill(getppid(),SIGUSR1));_exit(0);}
 wr_iot_rc_wait(&empty,&notification,&alarm_flag);assert(notification&&steps==2);
 assert(!sigprocmask(SIG_SETMASK,NULL,&check)&&sigismember(&check,SIGUSR1)==1);
 assert(!sigprocmask(SIG_SETMASK,&old,NULL));int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));notification=0;
 child=fork();assert(child>=0);
 if(!child){
  struct timespec now;assert(!clock_gettime(CLOCK_MONOTONIC,&now));
  struct wr_iot_control_result r={.id="01010101010101010101010101010101",.state=WR_IOT_RESULT_APPLIED,.created=(unsigned long long)now.tv_sec,.observed=(unsigned long long)now.tv_sec};
  assert(wr_iot_status_endpoint_query(directory,getppid(),geteuid(),&r));_exit(0);
 }
 for(unsigned i=0;i<4&&!observations;i++)wr_iot_rc_wait(&empty,&notification,&alarm_flag);
 assert(observations==1&&steps==2);assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 assert(wr_iot_status_endpoint_close(&endpoint));char path[256];assert(snprintf(path,sizeof(path),"%s/lock",directory)<(int)sizeof(path));assert(!unlink(path)&&!rmdir(directory));
 puts("PASS actual RC transient-init recovery and bounded retry; ppoll wait: notification priority, one phase per100ms, atomic pending-signal wake/mask restore and real child status query while idle; continuation/observer injected");
}
