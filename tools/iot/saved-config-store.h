/* RC-only requested configuration. This store never changes legacy loaded
 * profile keys, runtime gates, driver state or flash. A caller must retain its
 * ordinary operation/shutdown admission until finish or proven cancellation.
 * Experimental candidate stages this behind the typed configuration mailbox.
 */
#ifndef WR_IOT_SAVED_CONFIG_STORE_H
#define WR_IOT_SAVED_CONFIG_STORE_H
#include <sys/types.h>
#include <stdint.h>
#include "saved-config.h"
#define WR_IOT_SAVED_CONFIG_KEY "wr_iot_config_v1"
/* A source preparer may enable this only after checking the installed native
 * dump overflow guard. Default builds must not infer absence from a dump. */
#include "config-snapshot-prepared.h"
enum wr_iot_saved_store_phase {
 WR_IOT_SAVED_IDLE=0,WR_IOT_SAVED_PREPARED,WR_IOT_SAVED_UNCERTAIN,
 WR_IOT_SAVED_RAM_READY,WR_IOT_SAVED_CONFLICT,WR_IOT_SAVED_NO_SPACE
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
/* Capture one complete desired record under the caller-owned service guard.
 * Success sets present to 0 for proven absence, leaving config untouched, or
 * sets present to 1 and copies the decoded profile. Error leaves both outputs
 * unchanged. No legacy fallback, loaded-profile promotion or runtime action. */
int wr_iot_saved_config_capture(struct wr_iot_saved_config *,int *present);
/* Private immutable desired revision for a generation owner. It owns memory
 * only: caller retains admission/guard/file transaction and loaded provenance.
 * A changed desired tuple invalidates current(), never retargets this pin. */
struct wr_iot_generation_config {
 pid_t owner;uintptr_t self;int present;
 char id[33];unsigned long long created;
 char record[WR_IOT_SAVED_CONFIG_MAX];
};
int wr_iot_generation_config_capture(struct wr_iot_generation_config *,
 const char *,unsigned long long,struct wr_iot_saved_config *);
int wr_iot_generation_config_owned(const struct wr_iot_generation_config *);
int wr_iot_generation_config_current(const struct wr_iot_generation_config *,
 const char *,unsigned long long);
/* Releasing private observation memory never changes native/loaded state. */
int wr_iot_generation_config_release(struct wr_iot_generation_config *);
#endif
