#define _GNU_SOURCE
#include "control-mailbox.h"
#include <assert.h>
#include <stdlib.h>
#include <errno.h>
static void replace_result(int directory,const char *bytes,size_t length)
{
 int fd=openat(directory,"result",O_WRONLY|O_TRUNC|O_NOFOLLOW|O_CLOEXEC);
 assert(fd>=0&&write(fd,bytes,length)==(ssize_t)length&&!close(fd));
}
int main(void)
{
 char directory[]="/tmp/wr-config-mailbox-XXXXXX",bytes[160],changed[160],path[PATH_MAX];
 struct wr_iot_mailbox m;struct wr_iot_control_request request={0},claimed={0};
 struct wr_iot_control_result result={0};int fd;ssize_t n;
 assert(mkdtemp(directory));wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,directory,1));
 strcpy(request.id,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");request.created=100;
 request.operation=WR_IOT_OPERATION_CONFIG;
 request.request=(struct wr_iot_request){.enabled=0,.ssid="Disabled saved IoT",.password="saved-password",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};
 assert(wr_iot_mailbox_submit(&m,&request)&&wr_iot_mailbox_claim(&m,100,&claimed));
 assert(claimed.operation==WR_IOT_OPERATION_CONFIG&&!claimed.request.enabled&&claimed.request.password[0]);
 assert(!wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_APPLIED,101));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_RUNNING);
 assert(wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_RECOVERY,101));
 assert(!wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_STORED_RAM,102));
 assert(!wr_iot_mailbox_finish_continued(&m,request.id,101,getpid(),WR_IOT_RESULT_STORED_RAM,102));
 assert(!wr_iot_mailbox_finish_continued(&m,request.id,100,getpid()+1,WR_IOT_RESULT_STORED_RAM,102));
 assert(wr_iot_mailbox_finish_continued(&m,request.id,100,getpid(),WR_IOT_RESULT_STORED_RAM,102));
 assert(wr_iot_mailbox_finish_continued(&m,request.id,100,getpid(),WR_IOT_RESULT_STORED_RAM,103));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_STORED_RAM);
 assert(faccessat(m.directory,"request",F_OK,0)&&errno==ENOENT);
 fd=openat(m.directory,"result",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);assert(fd>=0);
 n=read(fd,bytes,sizeof(bytes));assert(n>0&&!close(fd));
 assert(!memcmp(bytes,"WR-IOT-RESULT-2\n",sizeof("WR-IOT-RESULT-2\n")-1));
 memcpy(changed,bytes,(size_t)n);changed[sizeof("WR-IOT-RESULT-")-1]='1';
 replace_result(m.directory,changed,(size_t)n);assert(!wr_iot_mailbox_result(&m,&result));
 replace_result(m.directory,bytes,(size_t)n);assert(wr_iot_mailbox_result(&m,&result));
 memset(&request,0,sizeof(request));strcpy(request.id,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");request.created=104;
 assert(wr_iot_mailbox_submit(&m,&request)&&wr_iot_mailbox_claim(&m,104,&claimed));
 assert(claimed.operation==WR_IOT_OPERATION_RUNTIME&&!claimed.request.ssid[0]);
 assert(!wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_STORED_RAM,105));
 assert(wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_APPLIED,105));
 wr_iot_mailbox_close(&m);
 for(int i=0;i<2;i++){
  assert(snprintf(path,sizeof(path),"%s/%s",directory,i?"lock":"result")<(int)sizeof(path));assert(!unlink(path));
 }
 assert(!rmdir(directory));
 puts("PASS actual shared mailbox: typed config/runtime terminal states cannot cross, exact continued RAM completion, cleanup retry, v1 cannot misread v2 RAM result, next runtime OFF accepted; no backend execution claim");
 return 0;
}
