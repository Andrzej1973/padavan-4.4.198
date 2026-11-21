#ifndef WR_IOT_RC_RUNTIME_H
#define WR_IOT_RC_RUNTIME_H
#include <signal.h>
struct wr_iot_rc_view_hooks {
 void (*init)(void);
 int (*ready_fd)(void);
 unsigned int (*delay_ms)(void);
 void (*step)(void);
};
int wr_iot_rc_runtime_register_view(const struct wr_iot_rc_view_hooks *);
/* Called only from PID1's existing main-loop wait, never a signal handler.
 * Existing SIGUSR1/SIGALRM flag handling stays in the vendor loop. */
struct wr_iot_control_request;
struct wr_iot_physical_stop_request;
/* Historical successful OFF receipt only, not current DOWN or ON permission. */
int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request *);
/* Private process-context admission only; no stock/UI OFF entry binding.
 * Terminal owner retained for the future verified SDK follow-up consumer. */
int wr_iot_rc_radio_off_begin(const struct wr_iot_control_request *,int);
void wr_iot_rc_wait(const sigset_t *,const volatile int *,const volatile int *);
#endif
