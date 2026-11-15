#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-disabled.h"
#include "rc-shutdown-admission.h"
static int cold_disabled_parent(struct wr_iot_cold_owner *p)
{
 return p&&p->owner==getpid()&&!p->busy&&p->phase==WR_COLD_OWNER_PREPARED&&
  p->generation.desired.enabled==0&&!p->generation.desired.ssid[0]&&
  !p->generation.desired.password[0]&&!p->generation.desired.gateway[0]&&
  !p->generation.desired.mask[0]&&!p->generation.desired.first[0]&&!p->generation.desired.last[0]&&
  wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&wr_iot_cold_owner_step(p)&&
  wr_iot_restart_disabled_profile_current();
}
int wr_iot_cold_disabled_current(struct wr_iot_cold_disabled *s)
{
 struct wr_iot_cold_owner *p;int ok;
 if(!s||s->owner!=getpid()||s->busy||!s->parent||!cold_disabled_parent(s->parent))return 0;
 p=s->parent;s->busy=1;
 ok=s->idle.owner==getpid()&&s->idle.ready&&s->idle.created==p->input.created&&
  !memcmp(s->idle.id,p->input.id,sizeof(s->idle.id))&&
  s->idle.idle.epoch==p->main.identity.adapter_epoch&&s->idle.idle.epoch>p->admission.down.epoch&&
  s->idle.idle.generation==p->main.identity.device_generation&&
  s->idle.idle.generation==p->admission.down.generation&&
  wr_iot_initial_off_observed(&s->idle)&&cold_disabled_parent(p);
 s->busy=0;return ok;
}
int wr_iot_cold_disabled_begin(struct wr_iot_cold_disabled *s,struct wr_iot_cold_owner *p)
{
 struct wr_iot_control_request request={0};
 if(!s||s->owner||s->busy||s->parent||s->idle.owner||!cold_disabled_parent(p))return 0;
 memcpy(request.id,p->input.id,sizeof(request.id));request.created=p->input.created;
 s->busy=1;
 if(!wr_iot_initial_off_begin(&s->idle,&request)){s->busy=0;return 0;}
 s->owner=getpid();s->parent=p;s->busy=0;
 return wr_iot_cold_disabled_current(s);
}
