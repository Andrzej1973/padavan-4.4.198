#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static volatile sig_atomic_t normal_shutdowns;
static void handler(int sig){if(!wr_iot_rc_shutdown_note(sig))normal_shutdowns++;}
int main(void)
{
 struct sigaction action={0};sigset_t before,current;
 action.sa_handler=handler;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,NULL));
 assert(!sigprocmask(SIG_SETMASK,NULL,&before));
 struct wr_iot_radio_stop_fence a={0},b={0};
 assert(wr_iot_radio_stop_fence_begin(&a)&&wr_iot_rc_shutdown.active);
 assert(!wr_iot_radio_stop_fence_begin(&a));
 assert(wr_iot_radio_stop_fence_begin(&b)&&b.level==2);
 assert(!wr_iot_radio_stop_fence_end(&a));
 assert(!kill(getpid(),SIGTERM)&&!normal_shutdowns);
 assert(wr_iot_radio_stop_fence_end(&b)&&wr_iot_rc_shutdown.active&&!normal_shutdowns);
 assert(wr_iot_radio_stop_fence_end(&a)&&!wr_iot_rc_shutdown.active&&normal_shutdowns==1);
 assert(!wr_iot_radio_stop_fence_end(&a));
 assert(!sigprocmask(SIG_SETMASK,NULL,&current));
 assert(sigismember(&before,SIGTERM)==sigismember(&current,SIGTERM));
 assert(sigismember(&before,SIGQUIT)==sigismember(&current,SIGQUIT));
 assert(wr_iot_rc_shutdown_begin());
 assert(!wr_iot_radio_stop_fence_begin(&a)&&wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_shutdown_end());
 assert(wr_iot_radio_stop_fence_begin(&a));
 assert(wr_iot_rc_shutdown_note(SIGTERM)&&normal_shutdowns==1);
 assert(wr_iot_radio_stop_fence_end(&a)&&normal_shutdowns==2);
 sigset_t blocked;sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);
 assert(!sigprocmask(SIG_BLOCK,&blocked,&before));
 assert(wr_iot_radio_stop_fence_begin(&a));assert(!kill(getpid(),SIGTERM));
 assert(wr_iot_radio_stop_fence_end(&a)&&normal_shutdowns==2);
 assert(!sigprocmask(SIG_SETMASK,NULL,&current)&&sigismember(&current,SIGTERM)==1);
 assert(!sigprocmask(SIG_SETMASK,&before,NULL)&&normal_shutdowns==3);
 puts("PASS nested radio-stop fence: LIFO/duplicate/busy refusal, queued SIGTERM delivered once at outer cleanup, original mask restored; no RF/DMA claim");
 return 0;
}
