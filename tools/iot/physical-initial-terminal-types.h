/* Adapter-owned persistent metadata only; no PID/kernel operations here. */
#ifndef WR_IOT_PHYSICAL_INITIAL_TERMINAL_TYPES_H
#define WR_IOT_PHYSICAL_INITIAL_TERMINAL_TYPES_H
#include "physical-initial-wire.h"
struct pid;
struct wr_iot_physical_initial_terminal {
 struct pid *owner;
 struct wr_iot_physical_initial_request request;
 unsigned status,ready,cleanup_phase;
};
#endif
