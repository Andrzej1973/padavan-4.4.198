/* PID identity only, not an adapter/module lifetime reference. */
#ifndef WR_IOT_PHYSICAL_STOP_TERMINAL_TYPES_H
#define WR_IOT_PHYSICAL_STOP_TERMINAL_TYPES_H
#include "physical-stop-wire.h"
struct pid;
/* Kernel-derived old Main completion identity. No pointer/reference or OPEN
 * permission; valid marks only the captured snapshot. A future handoff must
 * require terminal ready/RELEASED, exact PID/request and actual new registration. */
struct wr_iot_physical_stop_origin {
 unsigned long long main_generation,main_open_token,arm_epoch;
 unsigned long long ticket_serial,ticket_epoch,completion_epoch;
 unsigned int valid;
};
struct wr_iot_physical_stop_terminal {
 struct pid *owner;
 struct wr_iot_physical_stop_request request;
 unsigned int status,ready;
 struct wr_iot_physical_stop_origin origin;
};
#endif
