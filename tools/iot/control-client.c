#define _GNU_SOURCE
#include "control-channel.h"
#include <errno.h>
#ifndef WR_IOT_NOTIFY
#include <notify_rc.h>
#define WR_IOT_NOTIFY() notify_rc("wr_iot_apply")
#endif
static int random_id(char id[33]){
 unsigned char bytes[16];size_t offset=0;ssize_t n;int fd,i;
 fd=open("/dev/urandom",O_RDONLY|O_CLOEXEC);if(fd<0)return 0;
 while(offset<sizeof(bytes)){
  n=read(fd,bytes+offset,sizeof(bytes)-offset);
  if(n<0&&errno==EINTR)continue;
  if(n<=0){close(fd);return 0;}
  offset+=(size_t)n;
 }
 if(close(fd))return 0;
 for(i=0;i<16;i++)snprintf(id+i*2,3,"%02x",bytes[i]);
 memset(bytes,0,sizeof(bytes));return 1;
}
static int wr_iot_submit_record(struct wr_iot_control_request *record,char id[33]){
 struct wr_iot_mailbox m;int accepted=0;
 if(!record||!id)return 0;
 record->created=wr_iot_control_now();
 if(!record->created||!random_id(record->id))goto done;
 if(wr_iot_operation_is_edit(record->operation)){
  memcpy(record->edit.id,record->id,sizeof(record->id));record->edit.created=record->created;
 }
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,1))goto done;
 accepted=wr_iot_mailbox_submit(&m,record);wr_iot_mailbox_close(&m);
 if(accepted)memcpy(id,record->id,33);
 done:wr_iot_saved_wipe(record,sizeof(*record));
 /* The queue lock is released before notifying PID 1. A lost notification
  * cannot become applied; the stored request/result remain queued or unknown. */
 if(accepted)WR_IOT_NOTIFY();
 return accepted;
}
static int wr_iot_submit_request(const struct wr_iot_request *request,enum wr_iot_operation operation,char id[33]){
 struct wr_iot_control_request record={0};
 if(!request||!id)return 0;
 record.request=*request;record.operation=operation;return wr_iot_submit_record(&record,id);
}
int wr_iot_rc_submit(const struct wr_iot_request *request,char id[33])
{return wr_iot_submit_request(request,WR_IOT_OPERATION_RUNTIME,id);}
int wr_iot_rc_submit_config(const struct wr_iot_saved_config *config,char id[33])
{return config?wr_iot_submit_request(&config->profile,WR_IOT_OPERATION_CONFIG,id):0;}
int wr_iot_rc_submit_save(const struct wr_iot_saved_config *config,int explicit_save,char id[33])
{
 if(!config||(explicit_save!=0&&explicit_save!=1))return 0;
 return wr_iot_submit_request(&config->profile,explicit_save?WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT:
                              WR_IOT_OPERATION_CONFIG_SAVE_AUTO,id);
}
int wr_iot_rc_submit_edit(const struct wr_iot_saved_config *fields,const char *revision,
 enum wr_iot_config_edit_mode mode,enum wr_iot_config_key_action action,char id[33])
{
 struct wr_iot_control_request record={0};
 if(!fields||!id||!wr_iot_control_id(revision)||mode<WR_IOT_EDIT_RAM||mode>WR_IOT_EDIT_EXPLICIT)return 0;
 record.operation=WR_IOT_OPERATION_CONFIG_EDIT_RAM+mode;
 record.edit.fields=*fields;memcpy(record.edit.revision,revision,33);
 record.edit.mode=mode;record.edit.action=action;
 return wr_iot_submit_record(&record,id);
}
int wr_iot_rc_status(const char *id,struct wr_iot_control_result *out){
 struct wr_iot_mailbox m;struct wr_iot_control_result result,current;int observed;
 if(!out||!wr_iot_control_id(id))return 0;
 wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))return 0;
 observed=wr_iot_mailbox_result(&m,&result);wr_iot_mailbox_close(&m);
 if(observed!=1||strcmp(result.id,id))return 0;

 /* A terminal mailbox record is historical execution evidence. It cannot
  * establish current state after a legacy/manual/scheduled network change.
  * Observe outside the mailbox lock to preserve service/queue lock ordering. */
 if(result.state==WR_IOT_RESULT_APPLIED||result.state==WR_IOT_RESULT_STORED_RAM||result.state==WR_IOT_RESULT_SAVED_FLASH){
  if((result.state==WR_IOT_RESULT_APPLIED?wr_iot_activation_result_observed(&result):
      wr_iot_configuration_result_observed(&result))!=1)return 0;
  /* Observation released the queue lock. Reject a replaced or updated
   * transaction rather than publishing the earlier record as current. */
  if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))return 0;
  observed=wr_iot_mailbox_result(&m,&current);wr_iot_mailbox_close(&m);
  if(observed!=1||strcmp(current.id,result.id)||current.state!=result.state||
     current.created!=result.created||current.observed!=result.observed)return 0;
 }
 *out=result;return 1;
}
