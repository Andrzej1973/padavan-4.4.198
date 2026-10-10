#include <stdio.h>
#include <net/if.h>
#include <string.h>
#include <unistd.h>
#include "request-snapshot.h"
#include "service-guard.h"
#include "rc.h"

static const char *keys[]={
 "wr_iot_profile_t","wr_iot_network_t","wr_iot_firewall_t",
 "wr_iot_ssid_t","wr_iot_psk_t","wr_iot_gateway_t",
 "wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"
};
static int valid(const struct wr_iot_request_snapshot *s)
{
 return s&&s->active&&s->token==1&&s->owner==getpid();
}
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *s)
{
 struct wr_iot_request_snapshot candidate={0};
 size_t i,n;const char *value;
 if(!s||s->active||s->token)return 0;
 candidate.token=wr_iot_service_guard_enter(1);
 if(candidate.token!=1)return 0;
 /* An active/foreign bridge or service gate must be handled by teardown,
  * never captured as a baseline that rollback could inadvertently reactivate. */
 if(if_nametoindex("br-iot"))goto refused;
 for(i=0;i<9;i++){
  value=nvram_safe_get(keys[i]);n=strlen(value);
  if(n>=sizeof(candidate.values[i]) || (i<3&&n&&strcmp(value,"0")))goto refused;
  memcpy(candidate.values[i],value,n+1);
 }
 candidate.active=1;candidate.owner=getpid();*s=candidate;
 memset(&candidate,0,sizeof(candidate));return 1;
 refused:
 wr_iot_service_guard_leave(candidate.token);
 memset(&candidate,0,sizeof(candidate));return 0;
}
int wr_iot_request_snapshot_restore(struct wr_iot_request_snapshot *s)
{
 size_t i;int failed=0;
 if(!valid(s))return 0;
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
 token=s->token;
 memset(s,0,sizeof(*s));
 wr_iot_service_guard_leave(token);return 1;
}
