/* PID 1 IoT transaction signal admission. Signal handler touches only
 * sig_atomic_t fields; process faults retain the stock fatal path. */
#ifndef WR_IOT_RC_SHUTDOWN_ADMISSION_H
#define WR_IOT_RC_SHUTDOWN_ADMISSION_H
#include <signal.h>

struct wr_iot_rc_shutdown_admission {
 volatile sig_atomic_t active;
 volatile sig_atomic_t pending;
};
extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;

static inline int wr_iot_rc_shutdown_begin(void){
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 wr_iot_rc_shutdown.active=1;
 return 1;
}
/* Called by PID 1's signal handler. Defer only normal RC shutdown requests.
 * SIGPWR and process faults retain the stock immediate path.
 * Keep the first signal; do not call RC, malloc, logging or locks here. */
static inline int wr_iot_rc_shutdown_note(int sig){
 if(!wr_iot_rc_shutdown.active ||
    (sig!=SIGTERM
#ifdef SIGQUIT
     &&sig!=SIGQUIT
#endif
    ))return 0;
 if(!wr_iot_rc_shutdown.pending)wr_iot_rc_shutdown.pending=sig;
 return 1;
}
static inline int wr_iot_rc_shutdown_end(void){
 int pending;
 /* Once inactive, a new signal takes the stock path. Read the deferred
  * slot only after this switch so a late signal cannot be cleared unseen. */
 wr_iot_rc_shutdown.active=0;
 pending=wr_iot_rc_shutdown.pending;
 wr_iot_rc_shutdown.pending=0;
 return pending;
}
#endif
