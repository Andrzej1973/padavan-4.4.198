#ifndef WR_IOT_RESTART_RESUME_H
#define WR_IOT_RESTART_RESUME_H
#include "restart-restore.h"
#include "rc-quiesce.h"
enum wr_iot_restart_resume_phase {WR_RESUME_IDLE,WR_RESUME_RESTORE,WR_RESUME_REBIND,WR_RESUME_FINISH,WR_RESUME_DONE,WR_RESUME_RETAINED,WR_RESUME_SHUTDOWN,WR_RESUME_SHUTDOWN_CLOSED,WR_RESUME_CANCELLED,WR_RESUME_SHUTDOWN_ROLLBACK};
struct wr_iot_restart_resume {
 pid_t owner;int busy;unsigned long long created;
 enum wr_iot_restart_resume_phase phase;
 struct wr_iot_restart_restore restore;
 struct wr_iot_rc_quiesce shutdown;
 struct wr_iot_control_request stop_input;
};
/* Private process-context consumer AFTER exact physical RELEASE. Caller keeps
 * this at final address and supplies fresh nonzero ID/monotonic creation time.
 * No automatic scheduler binding or reinitialization of retained state. */
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume *,const unsigned char *,unsigned long long);
/* 1 completed resume,-1 completed cancellation,0 retained/in progress. */
int wr_iot_restart_resume_step(struct wr_iot_restart_resume *);
/* Fresh OFF envelope only, for pending normal shutdown after handoff.
 * CLOSED remains retained until a separate verified cancellation consumer. */
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume *,const struct wr_iot_control_request *);
/* Only consumed terminal state with no live resources; volatile private wipe.
 * Returns1 when reusable zero state established,0 leaves retained state. */
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume *);
#endif
