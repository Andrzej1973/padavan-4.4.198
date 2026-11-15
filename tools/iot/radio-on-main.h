#ifndef WR_IOT_RADIO_ON_MAIN_H
#define WR_IOT_RADIO_ON_MAIN_H
#include "radio-on-generation.h"
#include "restart-main-up.h"
#include "physical-rebind-controller.h"
enum wr_iot_on_main_phase {WR_ON_MAIN_IDLE,WR_ON_MAIN_WAIT,WR_ON_MAIN_NOT_SUBMITTED,WR_ON_MAIN_READY};
struct wr_iot_on_main {
 pid_t owner;int busy,bridge_attempted;
 enum wr_iot_on_main_phase phase;
 struct wr_iot_on_generation *generation;
 unsigned char open_id[16];struct wr_iot_driver_identity identity;
};
/* One administrative Main UP maximum, baseline retained on every outcome.
 * Even NOT_SUBMITTED may indicate foreign UP; never restore from that alone. */
int wr_iot_on_main_begin(struct wr_iot_on_main *,struct wr_iot_on_generation *,const unsigned char *);
/* Fresh software configuration proof; does not open ra2 or certify RF. */
int wr_iot_on_main_step(struct wr_iot_on_main *);
/* One bridge attach attempt; subsequent calls observe exact ra0/br0 only. */
int wr_iot_on_main_lan_step(struct wr_iot_on_main *);
#endif
