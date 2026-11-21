#define _GNU_SOURCE
#include "control-mailbox.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static void overwrite(struct wr_iot_mailbox *m,const char *bytes,size_t n)
{int fd=openat(m->directory,"result",O_WRONLY|O_TRUNC|O_CLOEXEC|O_NOFOLLOW);assert(fd>=0&&write(fd,bytes,n)==(ssize_t)n&&!close(fd));}
int main(void)
{
 char path[]="/tmp/wr-save-mailbox-XXXXXX",wire[512],bad[512],result_bytes[160],changed[160],file[PATH_MAX];
 struct wr_iot_control_request request={0},decoded={0},before;struct wr_iot_control_result result;
 struct wr_iot_mailbox mailbox;int n,fd,mode;ssize_t count;
 strcpy(request.id,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");request.created=100;
 request.request=(struct wr_iot_request){.enabled=0,.ssid="Saved IoT",.password="password123",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};
 for(mode=WR_IOT_OPERATION_CONFIG_SAVE_AUTO;mode<=WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;mode++){
  request.operation=mode;n=wr_iot_control_encode(wire,sizeof(wire),&request);assert(n>0&&!strstr(wire,"password123"));
  assert(!strncmp(wire,"WR-IOT-CONFIG-SAVE-1\n",21));
  assert(wr_iot_control_decode(&decoded,wire,n)&&decoded.operation==request.operation&&decoded.request.password[0]);
  before=decoded;memcpy(bad,wire,n+1);bad[0]='X';assert(!wr_iot_control_decode(&decoded,bad,n)&&!memcmp(&before,&decoded,sizeof(before)));
  assert(!wr_iot_control_decode(&decoded,wire,n-1)&&!memcmp(&before,&decoded,sizeof(before)));
 }
 assert(mkdtemp(path));wr_iot_mailbox_init(&mailbox);assert(wr_iot_mailbox_open(&mailbox,path,1));
 request.operation=WR_IOT_OPERATION_CONFIG_SAVE_AUTO;assert(wr_iot_mailbox_submit(&mailbox,&request));
 assert(wr_iot_mailbox_claim(&mailbox,100,&decoded)&&decoded.operation==WR_IOT_OPERATION_CONFIG_SAVE_AUTO);
 assert(!wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_APPLIED,101));
 assert(wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_RECOVERY,101));
 assert(!wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_SAVED_FLASH,102));
 assert(!wr_iot_mailbox_finish_continued(&mailbox,request.id,100,getpid()+1,WR_IOT_RESULT_SAVED_FLASH,102));
 assert(wr_iot_mailbox_finish_continued(&mailbox,request.id,100,getpid(),WR_IOT_RESULT_SAVED_FLASH,102));
 assert(wr_iot_mailbox_finish_continued(&mailbox,request.id,100,getpid(),WR_IOT_RESULT_SAVED_FLASH,103));
 assert(wr_iot_mailbox_result(&mailbox,&result)&&result.state==WR_IOT_RESULT_SAVED_FLASH);
 fd=openat(mailbox.directory,"result",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);assert(fd>=0);count=read(fd,result_bytes,sizeof(result_bytes));assert(count>0&&!close(fd));
 assert(!memcmp(result_bytes,"WR-IOT-RESULT-3\n",16));
 for(mode=1;mode<=2;mode++){memcpy(changed,result_bytes,count);changed[14]=(char)('0'+mode);overwrite(&mailbox,changed,count);assert(!wr_iot_mailbox_result(&mailbox,&result));}
 overwrite(&mailbox,result_bytes,count);assert(wr_iot_mailbox_result(&mailbox,&result));
 strcpy(request.id,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb");request.created=104;request.operation=WR_IOT_OPERATION_CONFIG;
 assert(wr_iot_mailbox_submit(&mailbox,&request)&&wr_iot_mailbox_claim(&mailbox,104,&decoded));
 assert(!wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_SAVED_FLASH,105));
 assert(wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_STORED_RAM,105));
 strcpy(request.id,"cccccccccccccccccccccccccccccccc");request.created=106;request.operation=WR_IOT_OPERATION_RUNTIME;memset(&request.request,0,sizeof(request.request));
 assert(wr_iot_mailbox_submit(&mailbox,&request)&&wr_iot_mailbox_claim(&mailbox,106,&decoded));
 assert(!wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_SAVED_FLASH,107));
 assert(wr_iot_mailbox_finish(&mailbox,request.id,WR_IOT_RESULT_APPLIED,107));
 wr_iot_mailbox_close(&mailbox);
 snprintf(file,sizeof(file),"%s/lock",path);assert(!unlink(file));snprintf(file,sizeof(file),"%s/result",path);assert(!unlink(file));assert(!rmdir(path));
 puts("PASS save codecs/shared mailbox: AUTO/EXPLICIT typed requests, exact continued flash result, v3 cannot cross v1/v2 or RAM/runtime operations; no RC/flash acceptance");return 0;
}
