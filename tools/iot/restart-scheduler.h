#ifndef WR_IOT_RESTART_SCHEDULER_H
#define WR_IOT_RESTART_SCHEDULER_H
/* PID1 process-context only. One stable private resume owner, no mailbox input.
 * This module alone installs no RC main-loop or restart entrypoint hook. */
int wr_iot_restart_scheduler_begin(const unsigned char *,unsigned long long);
/* Process context: fresh nonblocking entropy/monotonic identity only after
 * physical RELEASE. Refusal never invokes the restore owner. A failed begin
 * can retain ownership; inspect pending rather than retrying with another ID. */
int wr_iot_restart_scheduler_begin_fresh(void);
int wr_iot_restart_scheduler_pending(void);
int wr_iot_restart_scheduler_step(void);
int wr_iot_restart_scheduler_shutdown(const char *,unsigned long long);
int wr_iot_restart_scheduler_retire(void);
#endif
