#ifndef WR_IOT_COLD_ON_ADMISSION_H
#define WR_IOT_COLD_ON_ADMISSION_H
#include "radio-profile-state.h"
#include "physical-stop-wire.h"
#include "radio-stop-fence.h"
#include "precreated-down-observe.h"
enum wr_iot_cold_admission_phase {WR_COLD_IDLE,WR_COLD_REFUSED,WR_COLD_CAPTURED,WR_COLD_CANCELLED};
/* Private stable context. No fabricated RELEASE, generation, or Main UP. */
struct wr_iot_cold_admission {
 pid_t owner;int busy,guard;enum wr_iot_cold_admission_phase phase;
 unsigned char nonce[16];struct wr_iot_down_result down;
 struct wr_iot_radio_stop_fence fence;struct wr_iot_radio_profile_state profile;
};
/* 1 means fence claimed, including retained refusal. Caller must cancel or
 * retain the context; no native fallback after a claim. */
int wr_iot_cold_admission_begin(struct wr_iot_cold_admission *,const unsigned char *);
/* Exclusive generation borrower holds busy=1. Fresh DOWN, not profile hash. */
int wr_iot_cold_admission_origin_current(struct wr_iot_cold_admission *);
int wr_iot_cold_admission_current(struct wr_iot_cold_admission *);
/* Read-only capture only; generated or uncertain file state cannot cancel. */
int wr_iot_cold_admission_cancel(struct wr_iot_cold_admission *);
#endif
