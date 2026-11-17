#ifndef WR_IOT_CONFIG_OWNER_H
#define WR_IOT_CONFIG_OWNER_H
#include "saved-config-store.h"
#include "config-backend.h"
enum wr_iot_config_phase {
 WR_IOT_CONFIG_EMPTY=0,WR_IOT_CONFIG_WRITING,WR_IOT_CONFIG_RECOVERY,
 WR_IOT_CONFIG_RAM_READY,WR_IOT_CONFIG_REJECTED,WR_IOT_CONFIG_RAM_COMMITTED
};
struct wr_iot_config_owner {
 pid_t owner;uintptr_t self;int token,admitted,busy;
 char id[33];unsigned long long created;enum wr_iot_config_phase phase;
 struct wr_iot_config_backend backend;
 struct wr_iot_saved_store store;
 /* Private RAM receipt for fresh post-publication status, never returned or
  * logged. It retains configuration data already owned by the native store. */
 char expected[WR_IOT_SAVED_CONFIG_MAX];
};
int wr_iot_config_owner_begin(struct wr_iot_config_owner *,const char *,
 unsigned long long,const struct wr_iot_saved_config *);
enum wr_iot_config_phase wr_iot_config_owner_step(struct wr_iot_config_owner *,
 const char *,unsigned long long,int cancel);
/* Read-only status. Never calls step or invokes SET. */
int wr_iot_config_owner_observed(struct wr_iot_config_owner *,const char *,unsigned long long);
/* Caller publishes the exact terminal outcome before this cleanup. A failed
 * publication must retain this owner and call neither begin nor execute again.
 * Successful cleanup retains a private RAM receipt, not flash/runtime proof. */
int wr_iot_config_owner_finish(struct wr_iot_config_owner *,const char *,unsigned long long);
int wr_iot_config_owner_retire(struct wr_iot_config_owner *);
#endif
