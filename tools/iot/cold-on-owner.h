#ifndef WR_IOT_COLD_ON_OWNER_H
#define WR_IOT_COLD_ON_OWNER_H
#include "control-record.h"
#include "cold-on-main.h"
#include "cold-on-guest.h"
#include "cold-on-services.h"
#include "cold-on-multicast.h"
enum wr_iot_cold_owner_phase {WR_COLD_OWNER_IDLE,WR_COLD_OWNER_ADMITTED,WR_COLD_OWNER_GENERATE,
 WR_COLD_OWNER_MAIN_START,WR_COLD_OWNER_MAIN_WAIT,WR_COLD_OWNER_GUEST_BEGIN,WR_COLD_OWNER_GUEST,
 WR_COLD_OWNER_MC_BEGIN,WR_COLD_OWNER_MC,WR_COLD_OWNER_SERVICES_BEGIN,WR_COLD_OWNER_SERVICES,
 WR_COLD_OWNER_PREPARED,WR_COLD_OWNER_RESTORED,WR_COLD_OWNER_RETAINED};
/* Private stable-address context; never copy once claimed. PREPARED is only
 * the pre-IoT-OPEN continuation boundary, not ACTIVE/DONE or daemon readiness.
 * No backend/public entry, post-UP shutdown or root retirement binding yet. */
struct wr_iot_cold_owner {
 pid_t owner;int busy,reload;enum wr_iot_cold_owner_phase phase;
 struct wr_iot_control_request input;
 struct wr_iot_cold_admission admission;struct wr_iot_cold_generation generation;
 struct wr_iot_cold_main main;struct wr_iot_cold_guest guest;
 struct wr_iot_cold_multicast multicast;struct wr_iot_cold_services services;
};
/* 1 claims ownership even on retained admission refusal; no native fallback. */
int wr_iot_cold_owner_begin(struct wr_iot_cold_owner *,const struct wr_iot_control_request *,int);
/* One child phase per call. 1 only with a fresh PREPARED observation. */
int wr_iot_cold_owner_step(struct wr_iot_cold_owner *);
/* Pre-UP only; -1 restored but all ownership still retained. */
int wr_iot_cold_owner_recover(struct wr_iot_cold_owner *);
#endif
