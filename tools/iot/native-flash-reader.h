#ifndef WR_IOT_NATIVE_FLASH_READER_H
#define WR_IOT_NATIVE_FLASH_READER_H
#include "saved-config-flash.h"
/* Read-only observation, not a commit or durable-save receipt. Caller retains
 * expected revision ownership and must recheck currentness before publication.
 */
enum wr_iot_flash_config_result wr_iot_native_flash_compare(const char *,size_t);
#endif
