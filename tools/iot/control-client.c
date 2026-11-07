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
int wr_iot_rc_submit(const struct wr_iot_request *request,char id[33]){
 struct wr_iot_mailbox m;struct wr_iot_control_request record={0};int accepted;
 if(!request||!id)return 0;
 record.created=wr_iot_control_now();
 if(!record.created||!random_id(record.id))return 0;
 record.request=*request;wr_iot_mailbox_init(&m);
 if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,1)){
  memset(&record,0,sizeof(record));return 0;
 }
 accepted=wr_iot_mailbox_submit(&m,&record);wr_iot_mailbox_close(&m);
 if(accepted)memcpy(id,record.id,33);
 memset(&record,0,sizeof(record));
 /* The queue lock is released before notifying PID 1. A lost notification
  * cannot become applied; the stored request/result remain queued or unknown. */
 if(accepted)WR_IOT_NOTIFY();
 return accepted;
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
 if(result.state==WR_IOT_RESULT_APPLIED){
  if(wr_iot_activation_result_observed(&result)!=1)return 0;
  /* Observation released the queue lock. Reject a replaced or updated
   * transaction rather than publishing the earlier record as current. */
  if(!wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0))return 0;
  observed=wr_iot_mailbox_result(&m,&current);wr_iot_mailbox_close(&m);
  if(observed!=1||strcmp(current.id,result.id)||current.state!=result.state||
     current.created!=result.created||current.observed!=result.observed)return 0;
 }
 *out=result;return 1;
}
