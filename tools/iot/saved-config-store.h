/* RC-only requested configuration. This store never changes legacy loaded
 * profile keys, runtime gates, driver state or flash. A caller must retain its
 * ordinary operation/shutdown admission until finish or proven cancellation.
 * Not wired to HTTP/mailbox or installed by prepare-runtime yet.
 */
#ifndef WR_IOT_SAVED_CONFIG_STORE_H
#define WR_IOT_SAVED_CONFIG_STORE_H
#include <sys/types.h>
#include <stdint.h>
#include "saved-config.h"
#define WR_IOT_SAVED_CONFIG_KEY "wr_iot_config_v1"
/* A source preparer may enable this only after checking the installed native
 * dump overflow guard. Default builds must not infer absence from a dump. */
#ifndef WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED
#define WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED 0
#endif
enum wr_iot_saved_store_phase {
 WR_IOT_SAVED_IDLE=0,WR_IOT_SAVED_PREPARED,WR_IOT_SAVED_UNCERTAIN,
 WR_IOT_SAVED_RAM_READY,WR_IOT_SAVED_CONFLICT
};
struct wr_iot_saved_store {
 pid_t owner;uintptr_t self;int token,attempted,prior_present;
 enum wr_iot_saved_store_phase phase;
 char id[33];unsigned long long created;
 char prior[WR_IOT_SAVED_CONFIG_MAX],desired[WR_IOT_SAVED_CONFIG_MAX];
};
int wr_iot_saved_store_begin(struct wr_iot_saved_store *,const char *,
 unsigned long long,const struct wr_iot_saved_config *);
enum wr_iot_saved_store_phase wr_iot_saved_store_step(struct wr_iot_saved_store *);
/* Both functions reobserve the actual record; neither commits flash or ends
 * shutdown admission. Uncertain or foreign state retains the same owner. */
int wr_iot_saved_store_finish(struct wr_iot_saved_store *);
int wr_iot_saved_store_cancel(struct wr_iot_saved_store *);
/* Read-only current-record observation under a caller-owned service guard.
 * Unlike a store continuation this needs no active shutdown admission. */
int wr_iot_saved_record_current(const char *);
#endif
