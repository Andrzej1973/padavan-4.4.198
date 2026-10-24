/* Private, single-request HTTPD/RC mailbox. Paths are fixed by integration,
 * never HTTP input. All functions require an open, exclusively locked mailbox.
 * A claimed request survives process failure as RUNNING and blocks replacement.
 * This is not the service/activation guard; RC separately owns that guard. */
#ifndef WR_IOT_CONTROL_MAILBOX_H
#define WR_IOT_CONTROL_MAILBOX_H
#include <limits.h>
#include "control-record.h"
#include "service-lock.h"
struct wr_iot_mailbox {
 int directory;
 struct wr_iot_service_lock lock;
 char path[PATH_MAX],lock_path[PATH_MAX];
};
void wr_iot_mailbox_init(struct wr_iot_mailbox *);
int wr_iot_mailbox_open(struct wr_iot_mailbox *,const char *directory,int create);
void wr_iot_mailbox_close(struct wr_iot_mailbox *);
int wr_iot_mailbox_submit(struct wr_iot_mailbox *,const struct wr_iot_control_request *);
/* Only QUEUED can be claimed. Expired requests are rejected without execution. */
int wr_iot_mailbox_claim(struct wr_iot_mailbox *,unsigned long long now,
 struct wr_iot_control_request *);
/* Publish observed outcome. RECOVERY may only remain RECOVERY or become REJECTED
 * after confirmed rollback. Terminal cleanup is retryable without reexecution. */
int wr_iot_mailbox_finish(struct wr_iot_mailbox *,const char *id,
 enum wr_iot_result_state,unsigned long long now);
int wr_iot_mailbox_result(struct wr_iot_mailbox *,struct wr_iot_control_result *);
#endif
