/* Adapter metadata only; no transition operations or kernel reference calls. */
#ifndef WR_IOT_PHYSICAL_INITIAL_TYPES_H
#define WR_IOT_PHYSICAL_INITIAL_TYPES_H
#include "physical-initial-wire.h"
struct wr_iot_physical_initial_origin {
 const void *main_device,*iot_device;
 unsigned long epoch,generation,idle_serial,main_generation,main_open_token;
 unsigned long lifetime_serial;
};
struct wr_iot_physical_initial_record {
 unsigned long long serial;
 unsigned long completion_epoch;
 const void *task;
 struct wr_iot_physical_initial_request request;
 struct wr_iot_physical_initial_origin origin;
 unsigned status;
};
#endif
