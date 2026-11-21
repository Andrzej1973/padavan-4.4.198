/* Connected private AF_UNIX/SOCK_SEQPACKET status transport, no credentials.
 * Caller owns socket lifetime/path validation and schedules server on readable
 * readiness. Use UID0 and expected RC PID1 in production; explicit identities
 * permit real fork/socket tests without weakening the production call site.
 * Never reuse a connection after query failure/timeout. */
#ifndef WR_IOT_STATUS_CHANNEL_H
#define WR_IOT_STATUS_CHANNEL_H
#include <sys/types.h>
#include "control-record.h"
int wr_iot_status_query(int,pid_t,uid_t,const struct wr_iot_control_result *);
/* Return1 means a valid request was answered, including an explicit refusal. */
int wr_iot_status_serve_once(int,uid_t,int (*)(const struct wr_iot_control_result *));
#endif
