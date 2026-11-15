#ifndef WR_IOT_COLD_ON_MAIN_H
#define WR_IOT_COLD_ON_MAIN_H
#include "cold-on-generation.h"
#include "restart-main-up.h"
#include "driver-api-client.h"
enum wr_iot_cold_main_phase {WR_COLD_MAIN_IDLE,WR_COLD_MAIN_WAIT,WR_COLD_MAIN_NOT_SUBMITTED,WR_COLD_MAIN_READY};
struct wr_iot_cold_main {
 pid_t owner;int busy,bridge_attempted;enum wr_iot_cold_main_phase phase;
 struct wr_iot_cold_generation *generation;
 struct wr_iot_driver_identity identity;
};
/* One Main UP attempt. Possible submission permanently prohibits old rollback.
 * NOT_SUBMITTED may mean foreign Main UP and also retains ownership. */
int wr_iot_cold_main_begin(struct wr_iot_cold_main *,struct wr_iot_cold_generation *);
/* Existing typed initial-IDLE probe verifies new Main READY/configuration and
 * never-opened ra2. No OPEN/loaded-key/RF or future lifetime lease is claimed. */
int wr_iot_cold_main_step(struct wr_iot_cold_main *);
/* One ra0/br0 attach attempt; exact fresh membership and READY checked. */
int wr_iot_cold_main_lan_step(struct wr_iot_cold_main *);
#endif
