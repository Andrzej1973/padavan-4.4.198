#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include "rebind-start.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int depth,observations,takes,finishes,writes,fault;
int wr_iot_service_guard_enter(int enabled){assert(enabled);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_service_guard_dup(void){assert(depth);return open("/dev/null",O_RDONLY);}
int wr_iot_request_snapshot_take(struct wr_iot_request_snapshot *s)
{takes++;s->active=1;s->token=1;s->owner=getpid();depth++;return 1;}
int wr_iot_request_snapshot_finish(struct wr_iot_request_snapshot *s)
{finishes++;if(fault==2)return 0;assert(depth);depth--;memset(s,0,sizeof(*s));return 1;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request *p,const unsigned char *id,struct wr_iot_driver_identity *out)
{assert(depth&&p->action==WR_STOP_RELEASE&&id[0]==8);observations++;*out=(struct wr_iot_driver_identity){7,2};if(fault==1||fault==2||fault==4){if(observations==2)out->adapter_epoch++;}if(fault==5&&writes)out->adapter_epoch++;return 1;}
int wr_iot_request_stage_from(const char *(*read)(void *,const char *),void *context,int router,int radio,int mode)
{assert(depth&&read&&router==1&&radio==1&&!mode);(void)context;writes++;return fault!=3;}
static const char *reader(void *c,const char *k){(void)c;(void)k;return "1";}
#include "rebind-start.c"
int main(void)
{
 unsigned char id[16]={8};struct wr_iot_physical_stop_request physical={.action=WR_STOP_RELEASE};
 for(fault=0;fault<6;fault++){
  struct wr_iot_rebind_start s={0};depth=observations=takes=finishes=writes=0;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  if(fault==1||fault==2||fault==4){
   assert(!wr_iot_rebind_start_begin(&s,&physical,id)&&!s.admission.admitted&&!writes);
   if(fault==2){assert(s.admission.snapshot.active&&depth==1);fault=0;assert(wr_iot_request_snapshot_finish(&s.admission.snapshot));fault=2;}
   else assert(!depth&&!s.admission.snapshot.active);
   continue;
  }
  assert(wr_iot_rebind_start_begin(&s,&physical,id)&&depth==1&&!writes&&s.admission.reopened==2);
  assert(!wr_iot_rebind_start_begin(&s,&physical,id));
  assert(wr_iot_rebind_start_stage(&s,reader,0,1,1,0)==(fault==0));
  assert(s.admission.mutation_started&&s.admission.snapshot.active&&depth==1&&writes==1);
  assert(!wr_iot_rebind_start_stage(&s,reader,0,1,1,0)&&writes==1);
  assert(wr_iot_request_snapshot_finish(&s.admission.snapshot)&&!depth);
 }
 return 0;
}
