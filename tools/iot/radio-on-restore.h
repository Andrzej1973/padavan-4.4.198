#ifndef WR_IOT_RADIO_ON_RESTORE_H
#define WR_IOT_RADIO_ON_RESTORE_H
#include "radio-on-services.h"
#include "radio-on-multicast.h"
enum wr_iot_on_restore_phase {WR_ON_RESTORE_IDLE,WR_ON_RESTORE_PROFILE,WR_ON_RESTORE_MAIN_START,WR_ON_RESTORE_MAIN_WAIT,WR_ON_RESTORE_GUEST_BEGIN,WR_ON_RESTORE_GUEST_WAIT,WR_ON_RESTORE_MC_BEGIN,WR_ON_RESTORE_MC_WAIT,WR_ON_RESTORE_SERVICE_BEGIN,WR_ON_RESTORE_SERVICE_WAIT,WR_ON_RESTORE_PREPARED,WR_ON_RESTORE_HANDOFF,WR_ON_RESTORE_RETAINED};
/* Stable-address children. Parent admission must outlive the whole sequence. */
struct wr_iot_on_restore {
 pid_t owner;int busy,radio_state_attempted;unsigned long long handoff_created;
 enum wr_iot_on_restore_phase phase;unsigned char open_id[16];
 struct wr_iot_on_generation generation;
 struct wr_iot_on_main main;struct wr_iot_on_guest guest;
 struct wr_iot_on_services services;struct wr_iot_on_multicast multicast;
};
int wr_iot_on_restore_begin(struct wr_iot_on_restore *,struct wr_iot_on_admission *,const struct wr_iot_request *,int reload,const unsigned char *open_id);
/* One phase/tick.1 only PREPARED observations, never guard/receipt retirement. */
int wr_iot_on_restore_step(struct wr_iot_on_restore *);
#endif
