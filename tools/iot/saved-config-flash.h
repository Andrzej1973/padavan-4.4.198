/* Compare a desired revision with caller-supplied native image bytes.
 * No flash access, commit, runtime action or durability receipt is implied.
 */
#ifndef WR_IOT_SAVED_CONFIG_FLASH_H
#define WR_IOT_SAVED_CONFIG_FLASH_H
#include "saved-config.h"
#include "flash-image.h"
enum wr_iot_flash_config_result {
 WR_IOT_FLASH_CONFIG_INVALID=-1,WR_IOT_FLASH_CONFIG_ABSENT=0,
 WR_IOT_FLASH_CONFIG_DIFFERENT=1,WR_IOT_FLASH_CONFIG_MATCH=2
};
static inline enum wr_iot_flash_config_result wr_iot_saved_flash_compare(
 const void *bytes,size_t available,size_t capacity,
 const char *expected,size_t expected_length)
{
 struct wr_iot_saved_config decoded={0};
 char record[WR_IOT_SAVED_CONFIG_MAX]={0};
 char canonical[WR_IOT_SAVED_CONFIG_MAX]={0};
 enum wr_iot_flash_config_result result=WR_IOT_FLASH_CONFIG_INVALID;
 int found;size_t length;
 /* Decode/encode both sides: merely matching malformed bytes is no proof. */
 if(!wr_iot_saved_config_decode(&decoded,expected,expected_length)||
    !wr_iot_saved_config_encode(canonical,sizeof(canonical),&decoded)||
    strlen(canonical)!=expected_length||
    memcmp(canonical,expected,expected_length))goto done;
 found=wr_iot_flash_image_get(bytes,available,capacity,
    WR_IOT_SAVED_CONFIG_KEY,record,sizeof(record));
 if(found<0)goto done;
 if(!found){result=WR_IOT_FLASH_CONFIG_ABSENT;goto done;}
 length=strlen(record);
 if(!wr_iot_saved_config_decode(&decoded,record,length)||
    !wr_iot_saved_config_encode(canonical,sizeof(canonical),&decoded)||
    strlen(canonical)!=length||memcmp(canonical,record,length))goto done;
 result=length==expected_length&&!memcmp(record,expected,length)?
    WR_IOT_FLASH_CONFIG_MATCH:WR_IOT_FLASH_CONFIG_DIFFERENT;
 done:
 wr_iot_saved_wipe(&decoded,sizeof(decoded));
 wr_iot_saved_wipe(record,sizeof(record));
 wr_iot_saved_wipe(canonical,sizeof(canonical));
 return result;
}
#endif
