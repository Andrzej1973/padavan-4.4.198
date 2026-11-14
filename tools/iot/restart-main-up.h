#ifndef WR_IOT_RESTART_MAIN_UP_H
#define WR_IOT_RESTART_MAIN_UP_H
/* Transport outcome only. Caller records possible submission before calling
 * and must never replay after UNCERTAIN or RETURNED. Neither is readiness. */
enum wr_iot_restart_up_result {WR_RESTART_UP_NOT_SUBMITTED,
 WR_RESTART_UP_UNCERTAIN,WR_RESTART_UP_RETURNED};
enum wr_iot_restart_up_result wr_iot_restart_main_up(void);
#endif
