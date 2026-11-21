/* RC-local persistence composition, not a mailbox/WebUI route yet. Caller
 * retains the shared request's outer shutdown admission through publication.
 */
#ifndef WR_IOT_CONFIG_SAVE_OWNER_H
#define WR_IOT_CONFIG_SAVE_OWNER_H
#include "config-owner.h"
#include "flash-worker.h"
enum wr_iot_config_save_phase {
 WR_IOT_CONFIG_SAVE_EMPTY=0,WR_IOT_CONFIG_SAVE_STORING,WR_IOT_CONFIG_SAVE_SAVING,
 WR_IOT_CONFIG_SAVE_RECOVERY,WR_IOT_CONFIG_SAVE_RAM_ONLY,WR_IOT_CONFIG_SAVE_FLASH,
 WR_IOT_CONFIG_SAVE_REJECTED
};
enum wr_iot_config_save_reason {
 WR_IOT_CONFIG_SAVE_REASON_NONE=0,WR_IOT_CONFIG_SAVE_MANUAL_POLICY,
 WR_IOT_CONFIG_SAVE_CANCELLED,WR_IOT_CONFIG_SAVE_NO_CHILD,
 WR_IOT_CONFIG_SAVE_NOT_SUBMITTED
};
struct wr_iot_config_save_owner {
 pid_t owner;uintptr_t self;char id[33];unsigned long long created;
 enum wr_iot_flash_save_mode mode;enum wr_iot_config_save_phase phase,decision;
 enum wr_iot_config_save_reason reason;int busy,finished;
 struct wr_iot_config_owner ram;struct wr_iot_config_backend baseline;
 struct wr_iot_flash_worker worker;struct wr_iot_flash_worker_receipt proof;
};
int wr_iot_config_save_begin_admitted(struct wr_iot_config_save_owner *,const char *,
 unsigned long long,enum wr_iot_flash_save_mode,const struct wr_iot_saved_config *);
enum wr_iot_config_save_phase wr_iot_config_save_step(struct wr_iot_config_save_owner *,
 const char *,unsigned long long,int cancel);
/* Prepare private receipt/cleanup and recheck backend + RAM on every terminal
 * publication retry. Never reruns SET, fork or COMMIT after a decision. */
int wr_iot_config_save_terminal_ready(struct wr_iot_config_save_owner *,const char *,unsigned long long);
/* Historical confirmed save plus current RAM identity, not fresh flash I/O. */
int wr_iot_config_save_observed(struct wr_iot_config_save_owner *,const char *,unsigned long long);
/* Only after caller confirms terminal publication; keeps no private secrets. */
int wr_iot_config_save_retire(struct wr_iot_config_save_owner *);
#endif
