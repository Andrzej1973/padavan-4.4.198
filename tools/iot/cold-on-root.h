#ifndef WR_IOT_COLD_ON_ROOT_H
#define WR_IOT_COLD_ON_ROOT_H
#include "rc-cold-completion.h"
#include "rc-cold-disabled-completion.h"
#include "cold-on-postshutdown.h"
enum wr_iot_cold_root_phase {WR_COLD_ROOT_IDLE,WR_COLD_ROOT_PREPARE,
 WR_COLD_ROOT_HANDOFF,WR_COLD_ROOT_WAIT,WR_COLD_ROOT_CAPTURE,
 WR_COLD_ROOT_RELEASE,WR_COLD_ROOT_TERMINAL_BEGIN,WR_COLD_ROOT_TERMINAL,
 WR_COLD_ROOT_DONE,WR_COLD_ROOT_RETAINED};
/* Stable private parent for both intents. Never copy/reset while owned.
 * Normal completion only: scheduler entry and pending-shutdown routing must
 * be composed before installation. A retained failure never permits fallback. */
struct wr_iot_cold_root {
 pid_t owner;int busy,enabled;enum wr_iot_cold_root_phase phase;
 struct wr_iot_cold_owner parent;
 struct wr_iot_cold_handoff handoff;
 struct wr_iot_cold_release release;
 struct wr_iot_cold_parent_release released;
 struct wr_iot_cold_terminal terminal;
 struct wr_iot_cold_disabled disabled;
 struct wr_iot_cold_disabled_release disabled_release;
 struct wr_iot_cold_disabled_parent_release disabled_released;
 struct wr_iot_cold_disabled_terminal disabled_terminal;
 struct wr_iot_cold_stop stop;
};
/* 1 ownership claimed, including retained refusal. Does not mean ready. */
int wr_iot_cold_root_begin(struct wr_iot_cold_root *,const struct wr_iot_control_request *,int);
/* One child continuation per call; 1 only terminal software completion. */
int wr_iot_cold_root_step(struct wr_iot_cold_root *);
/* Repeat terminal's fresh proof before clearing only this completed root. */
int wr_iot_cold_root_retire(struct wr_iot_cold_root *);
/* Pending normal shutdown after attempted Main UP and before parent release.
 * off is required only to begin a bound backend shutdown; it must be a fresh
 * empty OFF envelope. Existing stop ownership is continued without new input.
 * 1 resources released and root wiped, 0 retained; no Main reset/rollback. */
int wr_iot_cold_root_shutdown(struct wr_iot_cold_root *,const struct wr_iot_control_request *off);
#endif
