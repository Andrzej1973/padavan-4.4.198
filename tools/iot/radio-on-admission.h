#ifndef WR_IOT_RADIO_ON_ADMISSION_H
#define WR_IOT_RADIO_ON_ADMISSION_H
#include "radio-profile-state.h"
#include "radio-stop-fence.h"
#include "physical-stop-wire.h"
enum wr_iot_on_admission_phase {WR_ON_ADMISSION_IDLE,WR_ON_ADMISSION_CAPTURED,WR_ON_ADMISSION_REFUSED,WR_ON_ADMISSION_CANCELLED,WR_ON_ADMISSION_RELEASED};
/* Stable private context. No Main UP is issued by this component. */
struct wr_iot_on_admission {pid_t owner;int busy,guard;enum wr_iot_on_admission_phase phase;struct wr_iot_radio_stop_fence fence;struct wr_iot_physical_stop_request released;struct wr_iot_radio_profile_state profile;};
/* Returns1 once fence is claimed, including retained preparation refusal. */
int wr_iot_on_admission_begin(struct wr_iot_on_admission *);
/* reload1 permits an older baseline: physical DOWN + exact capture required;
 * generated profile must be validated before Main UP. No generation here. */
int wr_iot_on_admission_begin_reload(struct wr_iot_on_admission *,int reload);
/* Read-only capture cancellation only; no generated profile may be discarded. */
int wr_iot_on_admission_cancel(struct wr_iot_on_admission *);
#endif
