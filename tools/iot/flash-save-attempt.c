#include <string.h>
#include <unistd.h>
#include "flash-save-attempt.h"
#include "control-record.h"

static int owned(const struct wr_iot_flash_save_attempt *attempt,const char *id,
 unsigned long long created)
{
 return getpid()>1&&attempt&&attempt->owner==getpid()&&
  attempt->self==(uintptr_t)attempt&&!attempt->busy&&id&&wr_iot_control_id(id)&&
  created&&created==attempt->created&&memchr(attempt->id,0,sizeof(attempt->id))&&
  !strcmp(attempt->id,id)&&memchr(attempt->expected,0,sizeof(attempt->expected))&&
  (attempt->mode==WR_IOT_FLASH_SAVE_AUTO||attempt->mode==WR_IOT_FLASH_SAVE_EXPLICIT)&&
  (attempt->attempted==0||attempt->attempted==1)&&
  (attempt->sealed==0||attempt->sealed==1)&&(!attempt->attempted||attempt->sealed)&&
  attempt->phase>=WR_IOT_FLASH_SAVE_PREPARED&&attempt->phase<=WR_IOT_FLASH_SAVE_MANUAL_PENDING;
}
int wr_iot_flash_save_begin(struct wr_iot_flash_save_attempt *attempt,const char *id,
 unsigned long long created,enum wr_iot_flash_save_mode mode,
 const char *expected,size_t length)
{
 struct wr_iot_saved_config checked={0};char canonical[WR_IOT_SAVED_CONFIG_MAX]={0};int ok=0;
 if(!attempt||attempt->owner||attempt->self||attempt->phase||attempt->attempted||attempt->sealed||attempt->busy||
    getpid()<=1||!id||!wr_iot_control_id(id)||!created||
    (mode!=WR_IOT_FLASH_SAVE_AUTO&&mode!=WR_IOT_FLASH_SAVE_EXPLICIT)||
    !wr_iot_saved_config_decode(&checked,expected,length)||
    !wr_iot_saved_config_encode(canonical,sizeof(canonical),&checked)||
    strlen(canonical)!=length||memcmp(canonical,expected,length))goto done;
 attempt->owner=getpid();attempt->self=(uintptr_t)attempt;
 memcpy(attempt->id,id,sizeof(attempt->id));attempt->created=created;attempt->mode=mode;
 memcpy(attempt->expected,canonical,length+1);attempt->phase=WR_IOT_FLASH_SAVE_PREPARED;ok=1;
 done:wr_iot_saved_wipe(&checked,sizeof(checked));wr_iot_saved_wipe(canonical,sizeof(canonical));return ok;
}
enum wr_iot_flash_save_phase wr_iot_flash_save_step(struct wr_iot_flash_save_attempt *attempt,
 const char *id,unsigned long long created)
{
 int manual=0,after=0;enum wr_iot_flash_config_result flash;
 if(!owned(attempt,id,created))return WR_IOT_FLASH_SAVE_UNCERTAIN;
 attempt->busy=1;
 if(!wr_iot_flash_save_snapshot(attempt->expected,&manual))goto uncertain;
 if(!attempt->attempted&&attempt->mode==WR_IOT_FLASH_SAVE_AUTO&&manual==1){
  attempt->sealed=1;attempt->phase=WR_IOT_FLASH_SAVE_MANUAL_PENDING;goto done;
 }
 /* A completed/skipped attempt never becomes another write if flash drifts. */
 flash=wr_iot_native_flash_compare(attempt->expected,strlen(attempt->expected));
 if(flash==WR_IOT_FLASH_CONFIG_INVALID)goto uncertain;
 if(flash!=WR_IOT_FLASH_CONFIG_MATCH&&!attempt->sealed&&!attempt->attempted){
  if(!wr_iot_flash_save_snapshot(attempt->expected,&after)||after!=manual)goto uncertain;
  attempt->attempted=1;attempt->sealed=1;attempt->phase=WR_IOT_FLASH_SAVE_UNCERTAIN;
  attempt->commit_return=wr_iot_flash_save_commit_once(attempt->expected,strlen(attempt->expected),attempt->mode);
  flash=wr_iot_native_flash_compare(attempt->expected,strlen(attempt->expected));
 }
 if(flash==WR_IOT_FLASH_CONFIG_MATCH&&(!attempt->attempted||attempt->commit_return==0)&&wr_iot_flash_save_snapshot(attempt->expected,&after)&&after==manual){
  attempt->sealed=1;attempt->phase=WR_IOT_FLASH_SAVE_OBSERVED;goto done;
 }
 uncertain:attempt->phase=WR_IOT_FLASH_SAVE_UNCERTAIN;
 done:attempt->busy=0;return attempt->phase;
}
