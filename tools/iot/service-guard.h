#ifndef WR_IOT_SERVICE_GUARD_H
#define WR_IOT_SERVICE_GUARD_H
/* RC is single-threaded. Return 1 held, 2 ungated bypass, 0 refused.
 * Every successful enter must have one matching leave. */
int wr_iot_service_guard_enter(int enabled);
void wr_iot_service_guard_leave(int token);
/* Caller owns returned duplicate; closing it never closes the outer guard. */
int wr_iot_service_guard_dup(void);
#endif
