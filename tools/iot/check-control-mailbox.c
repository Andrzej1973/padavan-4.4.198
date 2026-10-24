#define _GNU_SOURCE
#include "control-mailbox.h"
#include <assert.h>
#include <stdlib.h>
#include <errno.h>
static void path(char *out,const char *directory,const char *name){
 assert(snprintf(out,PATH_MAX,"%s/%s",directory,name)<PATH_MAX);
}
static void fixture_file(const char *name){
 int fd=open(name,O_WRONLY|O_CREAT|O_EXCL,0600);assert(fd>=0);
 assert(write(fd,"untouched",9)==9);assert(!close(fd));
}
static void unchanged(const char *name){
 char text[10]={0};int fd=open(name,O_RDONLY);assert(fd>=0);
 assert(read(fd,text,9)==9&&!strcmp(text,"untouched"));assert(!close(fd));
}
int main(void){
 char directory[]="/tmp/iot-control-mailbox-XXXXXX";
 char request_path[PATH_MAX],result_path[PATH_MAX],scratch[PATH_MAX],outside[PATH_MAX],alias[PATH_MAX];
 struct wr_iot_mailbox m,other;
 struct wr_iot_control_request request={0},claimed,before;
 struct wr_iot_control_result result;
 assert(mkdtemp(directory));path(request_path,directory,"request");
 path(result_path,directory,"result");path(outside,directory,"outside");
 path(alias,directory,"alias");
 wr_iot_mailbox_init(&m);wr_iot_mailbox_init(&other);
 assert(wr_iot_mailbox_open(&m,directory,1));
 assert(!wr_iot_mailbox_open(&other,directory,1));
 strcpy(request.id,"0123456789abcdef0123456789abcdef");request.created=100;
 /* Disabled requests are sufficient to exercise transport without a radio. */
 assert(wr_iot_mailbox_submit(&m,&request));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_QUEUED);
 assert(!wr_iot_mailbox_submit(&m,&request));
 memset(&claimed,0x5a,sizeof(claimed));before=claimed;
 assert(!wr_iot_mailbox_claim(&m,99,&claimed)&&!memcmp(&claimed,&before,sizeof(claimed)));
 assert(wr_iot_mailbox_claim(&m,101,&claimed)&&!strcmp(claimed.id,request.id));
 wr_iot_mailbox_close(&m);
 assert(wr_iot_mailbox_open(&m,directory,0));
 assert(!wr_iot_mailbox_claim(&m,102,&claimed));
 assert(!wr_iot_mailbox_submit(&m,&request));
 assert(wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_RECOVERY,103));
 assert(!access(request_path,F_OK));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_RECOVERY);
 assert(!wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_APPLIED,104));
 assert(!wr_iot_mailbox_submit(&m,&request));
 assert(wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_REJECTED,104));
 assert(access(request_path,F_OK)&&errno==ENOENT);
 assert(!wr_iot_mailbox_submit(&m,&request)); /* Do not reuse the prior ID. */
 request.id[0]='1';request.created=105;
 assert(wr_iot_mailbox_submit(&m,&request));
 memset(&claimed,0x5a,sizeof(claimed));before=claimed;
 assert(!wr_iot_mailbox_claim(&m,136,&claimed)&&!memcmp(&claimed,&before,sizeof(claimed)));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_REJECTED);
 assert(access(request_path,F_OK)&&errno==ENOENT);
 fixture_file(outside);
 assert(!symlink(outside,request_path));
 request.id[0]='2';request.created=140;
 assert(!wr_iot_mailbox_submit(&m,&request));
 assert(!wr_iot_mailbox_claim(&m,140,&claimed));unchanged(outside);
 assert(!unlink(request_path));
 assert(!chmod(result_path,0644));
 assert(!wr_iot_mailbox_result(&m,&result)&&!wr_iot_mailbox_submit(&m,&request));
 assert(!chmod(result_path,0600));
 assert(!link(result_path,alias));assert(!wr_iot_mailbox_result(&m,&result));assert(!unlink(alias));
 assert(!unlink(result_path)&&!symlink(outside,result_path));
 assert(!wr_iot_mailbox_submit(&m,&request));unchanged(outside);assert(!unlink(result_path));
 /* A foreign/stale publication file is never overwritten or removed. */
 path(scratch,directory,"result.new");fixture_file(scratch);
 assert(!wr_iot_mailbox_submit(&m,&request));unchanged(scratch);
 assert(!wr_iot_mailbox_claim(&m,141,&claimed));
 assert(!wr_iot_mailbox_submit(&m,&request));
 assert(!unlink(request_path)&&!unlink(scratch)); /* Fixture-owned incomplete publication. */
 assert(!chmod(directory,0755));assert(!wr_iot_mailbox_submit(&m,&request));assert(!chmod(directory,0700));
 assert(wr_iot_mailbox_submit(&m,&request));assert(wr_iot_mailbox_claim(&m,141,&claimed));
 assert(wr_iot_mailbox_finish(&m,request.id,WR_IOT_RESULT_APPLIED,142));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_APPLIED);
 wr_iot_mailbox_close(&m);
 assert(!unlink(result_path)&&!unlink(outside));path(scratch,directory,"lock");assert(!unlink(scratch));
 assert(!rmdir(directory));
 puts("PASS IoT mailbox: private ownership, lock contention, no replay, retained recovery, expiry, symlink/hardlink/mode refusal, fail-closed publication");
 return 0;
}
