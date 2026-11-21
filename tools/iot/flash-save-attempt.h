/* Child-only single-attempt flash save journal. Outer RC owner must retain
 * service/shutdown admission and this request identity across child lifetime.
 * A lost child result is never authorization to spawn a replacement commit.
 * Not connected to runtime or a WebUI route yet.
 */
#ifndef WR_IOT_FLASH_SAVE_ATTEMPT_H
#define WR_IOT_FLASH_SAVE_ATTEMPT_H
#include <sys/types.h>
#include "native-flash-reader.h"
enum wr_iot_flash_save_mode {WR_IOT_FLASH_SAVE_AUTO=1,WR_IOT_FLASH_SAVE_EXPLICIT=2};
enum wr_iot_flash_save_phase {
 WR_IOT_FLASH_SAVE_EMPTY=0,WR_IOT_FLASH_SAVE_PREPARED,
 WR_IOT_FLASH_SAVE_UNCERTAIN,WR_IOT_FLASH_SAVE_OBSERVED,
 WR_IOT_FLASH_SAVE_MANUAL_PENDING
};
struct wr_iot_flash_save_attempt {
 pid_t owner;uintptr_t self;char id[33];unsigned long long created;
 enum wr_iot_flash_save_mode mode;enum wr_iot_flash_save_phase phase;
 int attempted,sealed,busy,commit_return;
 char expected[WR_IOT_SAVED_CONFIG_MAX];
};
int wr_iot_flash_save_begin(struct wr_iot_flash_save_attempt *,const char *,
 unsigned long long,enum wr_iot_flash_save_mode,const char *,size_t);
enum wr_iot_flash_save_phase wr_iot_flash_save_step(struct wr_iot_flash_save_attempt *,
 const char *,unsigned long long);
/* Concrete adapters; called only from an owned non-PID1 attempt. */
int wr_iot_flash_save_snapshot(const char *,int *manual);
int wr_iot_flash_save_commit_once(const char *,size_t,enum wr_iot_flash_save_mode);
#endif
