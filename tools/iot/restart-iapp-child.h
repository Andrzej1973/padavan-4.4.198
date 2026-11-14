#ifndef WR_IOT_RESTART_IAPP_CHILD_H
#define WR_IOT_RESTART_IAPP_CHILD_H
#include <sys/types.h>
struct wr_iot_iapp_child {pid_t owner;int attempted,fd,result;};
/* Zero-init at final address. One fixed script restart. Caller must establish
 * service/firewall ownership before begin and retain it through uncertainty.
 * result1 means script exit0, not daemon readiness. No retry or PID killing. */
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child *);
/* 1 script returned0,-1 failed/missing receipt,0 pending. */
int wr_iot_iapp_child_step(struct wr_iot_iapp_child *);
#endif
