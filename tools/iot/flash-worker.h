#ifndef WR_IOT_FLASH_WORKER_H
#define WR_IOT_FLASH_WORKER_H
#include "flash-worker-wire.h"
enum wr_iot_flash_worker_phase {
 WR_IOT_FLASH_WORKER_EMPTY=0,WR_IOT_FLASH_WORKER_RUNNING,
 WR_IOT_FLASH_WORKER_OBSERVED,WR_IOT_FLASH_WORKER_MANUAL_PENDING,
 WR_IOT_FLASH_WORKER_UNKNOWN,WR_IOT_FLASH_WORKER_NOT_STARTED,
 WR_IOT_FLASH_WORKER_NOT_STORED
};
struct wr_iot_flash_worker {
 pid_t owner,child;uintptr_t self;int fd,busy,spawned;
 dev_t pipe_dev;ino_t pipe_ino;
 char id[33];unsigned long long created;enum wr_iot_flash_save_mode mode;
 enum wr_iot_flash_worker_phase phase;
 struct wr_iot_flash_worker_receipt receipt;
 char expected[WR_IOT_SAVED_CONFIG_MAX];
};
/* Caller retains exact request/backend/service/shutdown ownership. No second
 * begin is permitted after any fork attempt; UNKNOWN retains its journal.
 * Begin/step never wait for flash or a child in the parent process.
 */
int wr_iot_flash_worker_begin(struct wr_iot_flash_worker *,const char *,unsigned long long,
 enum wr_iot_flash_save_mode,const char *,size_t);
enum wr_iot_flash_worker_phase wr_iot_flash_worker_step(struct wr_iot_flash_worker *,
 const char *,unsigned long long);
/* Only after outer owner revalidates current request/RAM/backend. */
int wr_iot_flash_worker_retire(struct wr_iot_flash_worker *,const char *,unsigned long long);
#endif
