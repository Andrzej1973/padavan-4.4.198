/* Read-only admission before staging or network mutation. Serialized PID1
 * worker must already own rc-shutdown admission. Zero-initialize and retain
 * context; this is initial never-opened ra2 only, not reopen or RF proof. */
#ifndef WR_IOT_START_ADMISSION_H
#define WR_IOT_START_ADMISSION_H
#include "request-snapshot.h"
#include "precreated-idle-wire.h"
struct wr_iot_start_admission {
 struct wr_iot_request_snapshot snapshot;
 struct wr_iot_idle_result idle;
 int admitted,mutation_started,staged;
 int reopened; /* Post-CLOSE admission: never call initial-idle paths. */
};
int wr_iot_start_admission_begin(struct wr_iot_start_admission *,const unsigned char *);
/* Stage once through the existing guarded writer. Marks possible mutation
 * BEFORE dispatch, retaining baseline even if the writer partially fails. */
int wr_iot_start_admission_stage(struct wr_iot_start_admission *,const unsigned char *,
 const char *(*)(void *,const char *),void *,int,int,int);
/* Cancel only this read-only phase, before ANY staging/network/OPEN mutation.
 * After mutation the activation rollback owner must retain/recover snapshot. */
int wr_iot_start_admission_cancel(struct wr_iot_start_admission *);
#endif
