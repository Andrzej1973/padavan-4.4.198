/* Stable-address RC owner for a physical restart resume. Never copy while
 * retained: normal OFF points into the embedded runner. */
#ifndef WR_IOT_REBIND_OWNER_H
#define WR_IOT_REBIND_OWNER_H
#include "rebind-observe.h"
enum wr_iot_rebind_owner_phase {WR_REBIND_OWNER_IDLE,WR_REBIND_OWNER_START,
 WR_REBIND_OWNER_ACTIVE,WR_REBIND_OWNER_STOP,WR_REBIND_OWNER_OFF,WR_REBIND_OWNER_REJECTED};
struct wr_iot_rebind_owner {
 pid_t owner;
 int busy;
 enum wr_iot_rebind_owner_phase phase;
 struct wr_iot_rebind_runner start;
 struct wr_iot_rebind_active_stop stop;
};
int wr_iot_rebind_owner_begin(struct wr_iot_rebind_owner *,
 const struct wr_iot_control_request *,const struct wr_iot_physical_stop_request *,int,int,int);
/* Repeat physical restart only from fully completed/unowned OFF. Retains
 * previous completion on read-only refusal; never copies a live context. */
int wr_iot_rebind_owner_restart(struct wr_iot_rebind_owner *,
 const struct wr_iot_control_request *,const struct wr_iot_physical_stop_request *,int,int,int);
enum wr_iot_result_state wr_iot_rebind_owner_execute(struct wr_iot_rebind_owner *,
 const struct wr_iot_control_request *);
enum wr_iot_result_state wr_iot_rebind_owner_continue(struct wr_iot_rebind_owner *,
 const char *,unsigned long long);
int wr_iot_rebind_owner_observed(const struct wr_iot_rebind_owner *,const struct wr_iot_control_result *);
int wr_iot_rebind_owner_closed(const struct wr_iot_rebind_owner *,const struct wr_iot_control_result *,
 struct wr_iot_driver_closed_result *);
#endif
