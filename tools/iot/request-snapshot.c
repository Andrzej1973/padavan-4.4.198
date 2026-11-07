#include <stdio.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "request-snapshot.h"
#include "service-guard.h"
#include "bridge.h"
#include "rc.h"

static const char *keys[]={
 "wr_iot_profile_t","wr_iot_network_t","wr_iot_firewall_t",
 "wr_iot_ssid_t","wr_iot_psk_t","wr_iot_gateway_t",
 "wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"
};
static int valid(const struct wr_iot_request_snapshot *s)
{
 int fd;
 if(!s||!s->active||s->token!=1||s->owner!=getpid())return 0;
 fd=wr_iot_service_guard_dup();
 if(fd<0)return 0;
 return close(fd)==0;
}
static int take(struct wr_iot_request_snapshot *s,int disabling)
{
 struct wr_iot_request_snapshot candidate={0};
 size_t i,n;const char *value;
 if(!s||s->active||s->token)return 0;
 candidate.token=wr_iot_service_guard_enter(1);
 if(candidate.token!=1)return 0;
 /* An active/foreign bridge or service gate must be handled by teardown,
  * never captured as a baseline that rollback could inadvertently reactivate. */
 candidate.bridge_index=if_nametoindex("br-iot");
 if(disabling){
  if(!candidate.bridge_index||!wr_iot_bridge_is_owned())goto refused;
 }else if(candidate.bridge_index)goto refused;
 for(i=0;i<9;i++){
  value=nvram_safe_get(keys[i]);n=strlen(value);
  if(n>=sizeof(candidate.values[i]))goto refused;
  if(i<3&&((disabling&&strcmp(value,"0")&&strcmp(value,"1"))||
           (!disabling&&n&&strcmp(value,"0"))))goto refused;
  memcpy(candidate.values[i],value,n+1);
 }
 candidate.active=1;candidate.owner=getpid();candidate.disabling=disabling;
 if(disabling){memcpy(candidate.expected,candidate.values,sizeof(candidate.expected));candidate.expected_valid=1;}
 *s=candidate;
 memset(&candidate,0,sizeof(candidate));return 1;
 refused:
 wr_iot_service_guard_leave(candidate.token);
 memset(&candidate,0,sizeof(candidate));return 0;
}
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *s){return take(s,0);}
int wr_iot_request_disable_take(struct wr_iot_request_snapshot *s){return take(s,1);}
int wr_iot_request_disable_cancel(struct wr_iot_request_snapshot *s){
 int token;
 if(!valid(s)||!s->disabling||s->disable_mutated||s->disable_stage)return 0;
 token=s->token;memset(s,0,sizeof(*s));wr_iot_service_guard_leave(token);return 1;
}
static int expected_matches(const struct wr_iot_request_snapshot *s){
 size_t i;
 if(!s->expected_valid)return 0;
 for(i=0;i<9;i++)if(!memchr(s->expected[i],0,sizeof(s->expected[i]))||
    strcmp(nvram_safe_get(keys[i]),s->expected[i]))return 0;
 return 1;
}
static int clear_owned(struct wr_iot_request_snapshot *s,size_t first,size_t end){
 size_t i;int failed=0;const char *value,*desired;
 if(!expected_matches(s))return 0;
 for(i=first;i<end;i++){
  desired=i<3?"0":"";
  if(strcmp(s->expected[i],desired)){
   s->disable_mutated=1;
   failed |= nvram_set_temp(keys[i],desired)!=0;
   value=nvram_safe_get(keys[i]);
   /* A failing setter may have written its intended value. Accept only that
    * known result or the old expected value; never adopt an unknown writer. */
   if(!strcmp(value,desired))strcpy(s->expected[i],desired);
   else if(strcmp(value,s->expected[i]))return 0;
  }
  if(strcmp(s->expected[i],desired))failed=1;
 }
 return !failed&&expected_matches(s);
}
int wr_iot_request_disable_close_gates(struct wr_iot_request_snapshot *s){
 if(!valid(s)||!s->disabling||s->recovering||
    if_nametoindex("br-iot")!=s->bridge_index||!wr_iot_bridge_is_owned()||
    !wr_iot_bss_is_down())return 0;
 if(!clear_owned(s,0,3))return 0;
 s->disable_stage=1;return 1;
}
int wr_iot_request_disable_forget(struct wr_iot_request_snapshot *s){
 if(!valid(s)||!s->disabling||s->disable_stage<1||s->recovering||
    if_nametoindex("br-iot")||!wr_iot_bss_is_down())return 0;
 if(!clear_owned(s,3,9))return 0;
 s->disable_stage=2;return 1;
}
int wr_iot_request_disable_ready(struct wr_iot_request_snapshot *s){
 return valid(s)&&s->disabling&&s->disable_stage>=1&&!s->recovering&&
  expected_matches(s)&&!strcmp(s->expected[0],"0")&&
  !strcmp(s->expected[1],"0")&&!strcmp(s->expected[2],"0");
}
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot *s)
{
 size_t i;int failed=0;
 if(!valid(s)||s->disabling)return 0;
 s->recovering=1;s->restored=0;
 if(if_nametoindex("br-iot"))return 0;
 /* Close all service gates before restoring credentials/ranges. Attempt all
  * gates even if one setter fails; never restore a partially open snapshot. */
 for(i=0;i<3;i++)failed |= nvram_set_int_temp(keys[i],0)!=0;
 for(i=0;i<3;i++)failed |= strcmp(nvram_safe_get(keys[i]),"0")!=0;
 if(failed)return 0;
 for(i=3;i<9;i++)failed |= nvram_set_temp(keys[i],s->values[i])!=0;
 for(i=3;i<9;i++)failed |= strcmp(nvram_safe_get(keys[i]),s->values[i])!=0;
 if(failed)return 0;
 for(i=0;i<3;i++)failed |= nvram_set_temp(keys[i],s->values[i])!=0;
 for(i=0;i<3;i++)failed |= strcmp(nvram_safe_get(keys[i]),s->values[i])!=0;
 s->restored=!failed;return s->restored;
}
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *s)
{
 int token;
 if(!valid(s)||(s->recovering&&!s->restored))return 0;
 if(s->disabling&&(s->disable_stage!=2||if_nametoindex("br-iot")||
    !wr_iot_bss_is_down()||!expected_matches(s)))return 0;
 token=s->token;
 memset(s,0,sizeof(*s));
 wr_iot_service_guard_leave(token);return 1;
}
int wr_iot_request_snapshot_suspend(struct wr_iot_request_snapshot *s)
{
 size_t i,n;const char *value;
 if(!valid(s)||s->recovering||s->disabling)return 0;
 s->expected_valid=0;
 for(i=0;i<9;i++){
  value=nvram_safe_get(keys[i]);n=strlen(value);
  if(n>=sizeof(s->expected[i]))return 0;
  memcpy(s->expected[i],value,n+1);
 }
 s->expected_valid=1;
 s->token=0;
 wr_iot_service_guard_leave(1);
 return 1;
}
int wr_iot_request_snapshot_resume(struct wr_iot_request_snapshot *s)
{
 int token;size_t i;
 if(!s||!s->active||s->token||s->owner!=getpid()||s->recovering||s->disabling||!s->expected_valid)return 0;
 token=wr_iot_service_guard_enter(1);
 if(token!=1)return 0;
 for(i=0;i<9;i++){
  if(!memchr(s->expected[i],0,sizeof(s->expected[i]))||
     strcmp(nvram_safe_get(keys[i]),s->expected[i])){
   wr_iot_service_guard_leave(token);return 0;
  }
 }
 s->token=token;return 1;
}
