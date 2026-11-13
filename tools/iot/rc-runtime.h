#ifndef WR_IOT_RC_RUNTIME_H
#define WR_IOT_RC_RUNTIME_H
#include <signal.h>
/* Called only from PID1's existing main-loop wait, never a signal handler.
 * Existing SIGUSR1/SIGALRM flag handling stays in the vendor loop. */
void wr_iot_rc_wait(const sigset_t *,const volatile int *,const volatile int *);
#endif
