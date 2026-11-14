#ifndef WR_IOT_PHYSICAL_REBIND_PROBE_TYPES_H
#define WR_IOT_PHYSICAL_REBIND_PROBE_TYPES_H
#include "radio-transition.h"
#include "physical-stop-wire.h"
struct pid;
struct wr_iot_physical_rebind_probe {
 struct wr_iot_radio_ticket ticket;
 unsigned long main_generation,main_token;
 const struct pid *issuer;
 const void *main_device,*iot_device;
 struct wr_iot_physical_stop_request request;
 unsigned int active,accepted;
};
#endif
