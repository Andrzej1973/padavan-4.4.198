/* Retained same-process Save facade; separate from legacy RAM-only facade. */
#include <string.h>
#include <unistd.h>
#include "config-save-server.h"
#include "config-save-owner.h"
#include "native-flash-prepared.h"
#include "config-snapshot-prepared.h"
static struct wr_iot_config_save_owner save_owner;
static enum wr_iot_result_state outcome(enum wr_iot_config_save_phase phase)
{
 if(phase==WR_IOT_CONFIG_SAVE_REJECTED)return WR_IOT_RESULT_REJECTED;
 if(phase==WR_IOT_CONFIG_SAVE_RAM_ONLY)return WR_IOT_RESULT_STORED_RAM;
 if(phase==WR_IOT_CONFIG_SAVE_FLASH)return WR_IOT_RESULT_SAVED_FLASH;
 return WR_IOT_RESULT_RECOVERY;
}
enum wr_iot_result_state wr_iot_rc_save_execute(const struct wr_iot_control_request *request)
{
 struct wr_iot_saved_config config={0};int admitted;
 if(!request||!wr_iot_operation_is_save(request->operation))return WR_IOT_RESULT_REJECTED;
 if(save_owner.owner&&!wr_iot_config_save_retire(&save_owner))return WR_IOT_RESULT_RECOVERY;
 config.profile=request->request;
 admitted=wr_iot_config_save_begin_admitted(&save_owner,request->id,request->created,
  request->operation==WR_IOT_OPERATION_CONFIG_SAVE_AUTO?WR_IOT_FLASH_SAVE_AUTO:WR_IOT_FLASH_SAVE_EXPLICIT,&config);
 wr_iot_saved_wipe(&config,sizeof(config));
 return admitted?outcome(save_owner.phase):WR_IOT_RESULT_REJECTED;
}
enum wr_iot_result_state wr_iot_rc_save_continue(const char *id,unsigned long long created)
{return outcome(wr_iot_config_save_step(&save_owner,id,created,0));}
int wr_iot_rc_save_terminal_ready(const struct wr_iot_control_result *result)
{
 if(!result||!memchr(result->id,0,sizeof(result->id))||!wr_iot_control_id(result->id)||!result->created)return 0;
 if(!save_owner.owner)return result->state==WR_IOT_RESULT_REJECTED;
 if(save_owner.owner!=getpid()||strcmp(result->id,save_owner.id)||result->created!=save_owner.created||
    !save_owner.decision||outcome(save_owner.decision)!=result->state)return 0;
 return wr_iot_config_save_terminal_ready(&save_owner,result->id,result->created);
}
int wr_iot_rc_save_observed(const struct wr_iot_control_result *result)
{
 return result&&save_owner.finished&&save_owner.decision&&
  (result->state==WR_IOT_RESULT_STORED_RAM||result->state==WR_IOT_RESULT_SAVED_FLASH)&&
  result->state==outcome(save_owner.decision)&&memchr(result->id,0,sizeof(result->id))&&
  wr_iot_config_save_observed(&save_owner,result->id,result->created);
}
int wr_iot_rc_save_backend_install(void)
{
 const struct wr_iot_save_backend_hooks hooks={wr_iot_rc_save_execute,wr_iot_rc_save_continue,wr_iot_rc_save_terminal_ready};
 if(WR_IOT_NATIVE_FLASH_READBACK_PREPARED!=1||WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED!=1)return 0;
 return wr_iot_rc_register_save_backend(&hooks);
}
