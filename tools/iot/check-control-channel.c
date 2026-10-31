#define _GNU_SOURCE
#include "control-mailbox.h"
#include <assert.h>
#include <signal.h>
#include <stdlib.h>
static char test_directory[]="/tmp/iot-control-channel-XXXXXX";
static int notifications,executions;
static int observation_result=1,observations;
static int replace_during_observation;
static volatile sig_atomic_t shutdown_delivered;
static int defer_shutdown_once;
static char replacement_id[33];
static enum wr_iot_result_state backend_result=WR_IOT_RESULT_APPLIED;
static void notify_test(void);
#define WR_IOT_CONTROL_DIRECTORY test_directory
#define WR_IOT_NOTIFY() notify_test()
#include "control-client.c"
#include "control-server.c"
static void notify_test(void){notifications++;}
static void shutdown_test(int sig){
 assert(sig==SIGTERM);
 if(wr_iot_rc_shutdown_note(sig))return;
 shutdown_delivered++;
}
int wr_iot_activation_result_observed(const struct wr_iot_control_result *result){
 struct wr_iot_mailbox m;
 assert(result->state==WR_IOT_RESULT_APPLIED);observations++;
 /* The observer may take its service guard; queue lock must be released. */
 wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,test_directory,0));
 wr_iot_mailbox_close(&m);
 if(replace_during_observation){
  struct wr_iot_request request={0};
  replace_during_observation=0;
  assert(wr_iot_rc_submit(&request,replacement_id));
 }
 return observation_result;
}
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *request){
 struct wr_iot_control_result result;struct wr_iot_mailbox m;
 assert(!request->request.enabled&&wr_iot_control_id(request->id)&&request->created);executions++;
 wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,test_directory,0));
 assert(wr_iot_mailbox_result(&m,&result)&&result.state==WR_IOT_RESULT_RUNNING);
 assert(!strcmp(result.id,request->id)&&result.created==request->created);
 wr_iot_mailbox_close(&m);
 if(defer_shutdown_once){
  defer_shutdown_once=0;
  assert(raise(SIGTERM)==0);
  assert(!shutdown_delivered&&wr_iot_rc_shutdown.pending==SIGTERM);
  assert(signal(SIGTERM,shutdown_test)!=SIG_ERR);
 }
 /* A duplicate RC notification during execution cannot replay this request. */
 assert(!wr_iot_rc_dispatch());
 return backend_result;
}
int main(void){
 struct wr_iot_request request={0};struct wr_iot_control_result result;
 struct wr_iot_mailbox m;char id[33],other[33],path[PATH_MAX];
 assert(signal(SIGTERM,shutdown_test)!=SIG_ERR);
 assert(mkdtemp(test_directory));
 assert(wr_iot_rc_submit(&request,id)&&notifications==1&&wr_iot_control_id(id));
 assert(wr_iot_rc_status(id,&result)&&result.state==WR_IOT_RESULT_QUEUED);
 assert(!observations);
 assert(!wr_iot_rc_submit(&request,other)&&notifications==1);
 defer_shutdown_once=1;
 assert(wr_iot_rc_dispatch()&&executions==1&&shutdown_delivered==1);
 assert(wr_iot_rc_status(id,&result)&&result.state==WR_IOT_RESULT_APPLIED);
 assert(observations==1);
 observation_result=0;assert(!wr_iot_rc_status(id,&result));
 observation_result=-1;assert(!wr_iot_rc_status(id,&result));
 observation_result=2;assert(!wr_iot_rc_status(id,&result));
 observation_result=1;
 assert(wr_iot_rc_status(id,&result)&&result.state==WR_IOT_RESULT_APPLIED);
 assert(executions==1&&observations==5);
 assert(!wr_iot_rc_dispatch()&&executions==1);
 backend_result=WR_IOT_RESULT_RECOVERY;
 replace_during_observation=1;
 assert(!wr_iot_rc_status(id,&result));
 memcpy(other,replacement_id,sizeof(other));
 assert(notifications==2&&strcmp(id,other));
 assert(wr_iot_rc_status(other,&result)&&result.state==WR_IOT_RESULT_QUEUED);
 assert(!wr_iot_rc_status(id,&result));
 assert(wr_iot_rc_dispatch()&&executions==2);
 assert(wr_iot_rc_status(other,&result)&&result.state==WR_IOT_RESULT_RECOVERY);
 assert(!wr_iot_rc_submit(&request,id)&&!wr_iot_rc_dispatch()&&executions==2);
 /* Only emulate explicit confirmed recovery; the real backend is absent. */
 wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,test_directory,0));
 assert(wr_iot_mailbox_finish(&m,other,WR_IOT_RESULT_REJECTED,wr_iot_control_now()));
 wr_iot_mailbox_close(&m);
 assert(snprintf(path,sizeof(path),"%s/result",test_directory)<(int)sizeof(path));assert(!unlink(path));
 assert(snprintf(path,sizeof(path),"%s/lock",test_directory)<(int)sizeof(path));assert(!unlink(path));
 assert(!rmdir(test_directory));
 puts("PASS IoT control channel: fixed notification, queued/running/applied separation, no duplicate execution, retained recovery, private result IDs");
 return 0;
}
