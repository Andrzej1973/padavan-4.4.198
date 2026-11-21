#ifndef WR_IOT_RESTART_AUTH_STOP_H
#define WR_IOT_RESTART_AUTH_STOP_H
#include <sys/types.h>
enum wr_iot_auth_stop_phase {WR_AUTH_IDLE,WR_AUTH_TERM_WAIT,WR_AUTH_KILL_WAIT,WR_AUTH_STOPPED,WR_AUTH_RETAINED};
struct wr_iot_auth_stop {pid_t owner;int busy;unsigned attempted;unsigned long long deadline,last;enum wr_iot_auth_stop_phase phase;};
/* Caller supplies CLOCK_MONOTONIC milliseconds. Fixed SDK service only.
 * Adapters must check service ownership/guard and never sleep. Name absence is
 * an administrative prerequisite, not PID ownership or RF/DMA completion. */
int wr_iot_auth_stop_present(void); /* -1 unknown,0 absent,1 present */
int wr_iot_auth_stop_signal(int); /* one fixed-service signal command */
int wr_iot_auth_stop_begin(struct wr_iot_auth_stop *,unsigned long long);
int wr_iot_auth_stop_step(struct wr_iot_auth_stop *,unsigned long long);
#endif
