#ifndef WR_IOT_COLD_ON_SCHEDULER_H
#define WR_IOT_COLD_ON_SCHEDULER_H
struct wr_iot_control_request;
/* Private PID1 cold-root slot. Claim is not completion or native fallback
 * permission. The stock radio-entry selector is a separate binding. */
int wr_iot_rc_cold_on_begin(const struct wr_iot_control_request *,int reload);
int wr_iot_cold_on_pending(void);
/* 1 software DONE still owned; -1 checked cancellation released the slot. */
int wr_iot_cold_on_step(void);
int wr_iot_cold_on_retire(void);
#endif
