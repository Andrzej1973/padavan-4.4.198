/* PID identity only, not an adapter/module lifetime reference. */
#ifndef WR_IOT_PHYSICAL_STOP_TERMINAL_TYPES_H
#define WR_IOT_PHYSICAL_STOP_TERMINAL_TYPES_H
#include "physical-stop-wire.h"
struct pid;
struct wr_iot_physical_stop_terminal {
 struct pid *owner;
 struct wr_iot_physical_stop_request request;
 unsigned int status,ready;
};
#endif
