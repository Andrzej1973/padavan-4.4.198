/* RC-local configuration operation behind the existing single mailbox slot.
 * The mailbox server retains its shutdown admission through terminal result
 * publication. No additional queue, writer, activation or flash path exists. */
#include <string.h>
#include <unistd.h>
#include "control-channel.h"
#include "config-owner.h"
static struct wr_iot_config_owner configuration;
static enum wr_iot_result_state outcome(enum wr_iot_config_phase phase)
{
 if(phase==WR_IOT_CONFIG_REJECTED)return WR_IOT_RESULT_REJECTED;
 if(phase==WR_IOT_CONFIG_RAM_READY||phase==WR_IOT_CONFIG_RAM_COMMITTED)return WR_IOT_RESULT_STORED_RAM;
 return WR_IOT_RESULT_RECOVERY;
}
enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *request)
{
 struct wr_iot_saved_config config={0};int admitted;
 if(!request||request->operation!=WR_IOT_OPERATION_CONFIG)return WR_IOT_RESULT_REJECTED;
 if(configuration.owner&&!wr_iot_config_owner_retire(&configuration))return WR_IOT_RESULT_RECOVERY;
 config.profile=request->request;
 admitted=wr_iot_config_owner_begin_admitted(&configuration,request->id,request->created,&config);
 wr_iot_saved_wipe(&config,sizeof(config));
 return admitted?outcome(configuration.phase):WR_IOT_RESULT_REJECTED;
}
enum wr_iot_result_state wr_iot_rc_config_continue(const char *id,unsigned long long created)
{return outcome(wr_iot_config_owner_step(&configuration,id,created,0));}
int wr_iot_rc_config_observed(const struct wr_iot_control_result *result)
{
 return result&&result->state==WR_IOT_RESULT_STORED_RAM&&
  memchr(result->id,0,sizeof(result->id))&&configuration.phase==WR_IOT_CONFIG_RAM_COMMITTED&&
  !configuration.admitted&&wr_iot_config_owner_observed(&configuration,result->id,result->created);
}
int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *result)
{
 if(!result||!memchr(result->id,0,sizeof(result->id))||
    !wr_iot_control_id(result->id)||!result->created)return 0;
 if(result->state!=WR_IOT_RESULT_STORED_RAM&&result->state!=WR_IOT_RESULT_REJECTED)return 0;
 if(!configuration.owner)return result->state==WR_IOT_RESULT_REJECTED;
 if(configuration.owner!=getpid()||strcmp(configuration.id,result->id)||
    configuration.created!=result->created)return 0;
 if(result->state==WR_IOT_RESULT_REJECTED&&configuration.phase!=WR_IOT_CONFIG_REJECTED)return 0;
 if(result->state==WR_IOT_RESULT_STORED_RAM&&configuration.phase!=WR_IOT_CONFIG_RAM_READY&&
    configuration.phase!=WR_IOT_CONFIG_RAM_COMMITTED)return 0;
 if(configuration.admitted){
  if(!wr_iot_config_owner_observed(&configuration,result->id,result->created)||
     !wr_iot_config_owner_finish(&configuration,result->id,result->created))return 0;
 }
 /* Cleanup precedes public terminal publication, but the shared server still
  * owns admission. A failed publication keeps this private receipt and never
  * repeats SET; every retry rechecks the current record. */
 return result->state==WR_IOT_RESULT_REJECTED||wr_iot_rc_config_observed(result);
}
