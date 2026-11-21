/* Retained single-task RC transaction. Zero-initialize; never copy a live
 * session. Each advance performs at most one existing ioctl operation.
 * Caller retains shutdown/service admission until terminal acknowledgment.
 * Completion is a driver receipt, not physical runtime acceptance. */
#ifndef WR_IOT_PHYSICAL_STOP_SESSION_H
#define WR_IOT_PHYSICAL_STOP_SESSION_H
#include <sys/types.h>
#include "physical-stop-client.h"
enum wr_iot_physical_session_phase {
 WR_PHYSICAL_SESSION_IDLE,WR_PHYSICAL_SESSION_ARM,
 WR_PHYSICAL_SESSION_DOWN,WR_PHYSICAL_SESSION_QUERY,
 WR_PHYSICAL_SESSION_CANCEL,WR_PHYSICAL_SESSION_RELEASE,
 WR_PHYSICAL_SESSION_COMPLETE,WR_PHYSICAL_SESSION_CANCELLED
};
struct wr_iot_physical_session {
 pid_t owner;
 int busy;
 enum wr_iot_physical_session_phase phase;
 struct wr_iot_physical_stop_request request;
};
int wr_iot_physical_session_begin(struct wr_iot_physical_session *,
 const struct wr_iot_physical_stop_request *);
/* Returns 1 only after RELEASE acknowledgment, -1 after CANCEL acknowledgment,
 * zero while retained or on invalid/foreign/reentrant access. No implicit retry
 * of DOWN, no interface UP and no timeout-based permission to reopen. */
int wr_iot_physical_session_advance(struct wr_iot_physical_session *);
#endif
