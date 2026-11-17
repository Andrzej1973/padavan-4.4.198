#define _GNU_SOURCE
#include "control-channel.h"
#include "rc-shutdown-admission.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int runtime_calls,config_calls,observations;
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *r){assert(r->operation==WR_IOT_OPERATION_RUNTIME);runtime_calls++;return WR_IOT_RESULT_APPLIED;}
enum wr_iot_result_state wr_iot_activation_continue(const char *id,unsigned long long time){(void)id;(void)time;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_backend_applied_route(const char *id,unsigned long long time){assert(wr_iot_control_id(id)&&time);return 1;}
enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *r){(void)r;config_calls++;return WR_IOT_RESULT_STORED_RAM;}
enum wr_iot_result_state wr_iot_rc_config_continue(const char *id,unsigned long long time){(void)id;(void)time;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *r){return r&&r->state==WR_IOT_RESULT_STORED_RAM;}
int wr_iot_activation_result_observed(const struct wr_iot_control_result *r){(void)r;observations++;return 1;}
int wr_iot_configuration_result_observed(const struct wr_iot_control_result *r){observations++;return r->state==WR_IOT_RESULT_STORED_RAM;}
static int save_calls,save_steps,save_terminals;
static enum wr_iot_result_state save_execute(const struct wr_iot_control_request *r)
{assert(wr_iot_operation_is_save(r->operation));save_calls++;return WR_IOT_RESULT_RECOVERY;}
static enum wr_iot_result_state save_progress(const char *id,unsigned long long created)
{assert(wr_iot_control_id(id)&&created);save_steps++;return WR_IOT_RESULT_SAVED_FLASH;}
static int save_terminal(const struct wr_iot_control_result *r)
{assert(r->state==WR_IOT_RESULT_SAVED_FLASH);save_terminals++;return 1;}
int main(void){
 struct wr_iot_mailbox m;struct wr_iot_control_request r={0},claimed;struct wr_iot_control_result result;
 char file[PATH_MAX];int mode;
 r.request=(struct wr_iot_request){.enabled=0,.ssid="IoT save",.password="password123",.gateway="192.168.50.1",
 .mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"};
 for(mode=WR_IOT_OPERATION_CONFIG_SAVE_AUTO;mode<=WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;mode++){
  memset(r.id,mode==WR_IOT_OPERATION_CONFIG_SAVE_AUTO?'a':'b',32);r.id[32]=0;r.created=wr_iot_control_now();r.operation=mode;
  wr_iot_mailbox_init(&m);assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,1)&&wr_iot_mailbox_submit(&m,&r));wr_iot_mailbox_close(&m);
  assert(wr_iot_rc_dispatch());assert(!wr_iot_rc_pending()&&!runtime_calls&&!config_calls);
  assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_result(&m,&result));
  assert(result.state==WR_IOT_RESULT_REJECTED);wr_iot_mailbox_close(&m);
 }
 memset(r.id,'c',32);r.created=wr_iot_control_now();r.operation=WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;
 assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_submit(&m,&r));
 assert(wr_iot_mailbox_claim(&m,r.created,&claimed)&&wr_iot_mailbox_finish(&m,r.id,WR_IOT_RESULT_SAVED_FLASH,r.created));wr_iot_mailbox_close(&m);
 assert(!wr_iot_rc_status(r.id,&result)&&observations==1); /* No unsupported flash status success. */
 {
 struct wr_iot_save_backend_hooks hooks={save_execute,save_progress,save_terminal},bad=hooks;
 bad.progress=NULL;assert(!wr_iot_rc_register_save_backend(&bad));
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_rc_register_save_backend(&hooks));wr_iot_rc_shutdown.active=0;
 assert(wr_iot_rc_register_save_backend(&hooks));assert(!wr_iot_rc_register_save_backend(&hooks));
 memset(r.id,'d',32);r.created=wr_iot_control_now();r.operation=WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT;
 assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_submit(&m,&r));wr_iot_mailbox_close(&m);
 assert(wr_iot_rc_dispatch()&&wr_iot_rc_pending()&&save_calls==1&&!runtime_calls&&!config_calls);
 assert(!wr_iot_rc_register_save_backend(&hooks));
 assert(wr_iot_rc_continue()&&!wr_iot_rc_pending()&&save_steps==1&&save_terminals==1);
 assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0)&&wr_iot_mailbox_result(&m,&result));
 assert(result.state==WR_IOT_RESULT_SAVED_FLASH);wr_iot_mailbox_close(&m);
 assert(!wr_iot_rc_continue()&&save_calls==1&&save_steps==1);
 }
 {
 struct wr_iot_saved_config config={0};char queued[33];config.profile=r.request;
 assert(!wr_iot_rc_submit_save(&config,2,queued));
 for(int explicit_save=0;explicit_save<=1;explicit_save++){
  assert(wr_iot_rc_submit_save(&config,explicit_save,queued));
  assert(wr_iot_mailbox_open(&m,WR_IOT_CONTROL_DIRECTORY,0));
  assert(wr_iot_mailbox_claim(&m,wr_iot_control_now(),&claimed));
  assert(claimed.operation==(explicit_save?WR_IOT_OPERATION_CONFIG_SAVE_EXPLICIT:WR_IOT_OPERATION_CONFIG_SAVE_AUTO));
  assert(wr_iot_mailbox_finish(&m,queued,WR_IOT_RESULT_REJECTED,wr_iot_control_now()));wr_iot_mailbox_close(&m);
 }
 }
 snprintf(file,sizeof(file),"%s/result",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));
 snprintf(file,sizeof(file),"%s/lock",WR_IOT_CONTROL_DIRECTORY);assert(!unlink(file));assert(!rmdir(WR_IOT_CONTROL_DIRECTORY));
 puts("PASS actual unbound RC/client: typed Save cannot enter runtime/config executors; flash status refuses without observer; no device or flash execution");return 0;
}
