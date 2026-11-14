#define _GNU_SOURCE
#include <unistd.h>
#include "restart-multicast-controller.h"
#include "restart-multicast.h"
#include "rc-shutdown-admission.h"
static int mc_same(const struct wr_iot_multicast_policy*a,const struct wr_iot_multicast_policy*b)
{return a->required==b->required&&a->enabled==b->enabled&&a->guest==b->guest;}
static int mc_owners(struct wr_iot_restart_main*m,struct wr_iot_restart_guest*g)
{return m&&g&&g->main==m&&wr_iot_restart_main_lan_step(m)&&wr_iot_restart_guest_step(g);}
int wr_iot_restart_multicast_begin(struct wr_iot_multicast*s,struct wr_iot_restart_main*m,struct wr_iot_restart_guest*g)
{
 struct wr_iot_multicast_policy p;
 if(!s||!m||!g||s->owner||s->busy||s->phase!=WR_MC_IDLE||s->next||s->attempted||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!mc_owners(m,g)||
    !wr_iot_rc_restart_multicast_policy(&p)||wr_iot_rc_shutdown.pending)return 0;
 s->owner=getpid();s->main=m;s->guest=g;s->policy=p;s->phase=p.required?WR_MC_SUBMIT:WR_MC_READY;return 1;
}
int wr_iot_restart_multicast_step(struct wr_iot_multicast*s)
{
 struct wr_iot_multicast_policy p;int ready=0;
 if(!s||s->owner!=getpid()||s->busy||!s->main||!s->guest||
    (s->phase!=WR_MC_SUBMIT&&s->phase!=WR_MC_READY)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 s->busy=1;
 if(!mc_owners(s->main,s->guest)||!wr_iot_rc_restart_multicast_policy(&p)||
    !mc_same(&s->policy,&p)||wr_iot_rc_shutdown.pending)goto done;
 if(s->phase==WR_MC_READY){
  ready=!p.required||(s->attempted==(p.guest?3U:1U)&&
    wr_iot_restart_multicast_current(0,p.enabled)&&
    (!p.guest||wr_iot_restart_multicast_current(1,p.enabled)));
  goto done;
 }
 if(s->next>1||(s->next==1&&!p.guest)||(s->attempted&(1U<<s->next)))goto done;
 s->attempted|=1U<<s->next;s->phase=WR_MC_UNCERTAIN;
 if(!wr_iot_restart_multicast_apply(s->next,p.enabled))goto done;
 s->next++;s->phase=(s->next==(p.guest?2U:1U))?WR_MC_READY:WR_MC_SUBMIT;
 done:s->busy=0;return ready;
}

int wr_iot_restart_multicast_observed(struct wr_iot_multicast*s)
{
 struct wr_iot_multicast_policy p;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_MC_READY||
    !s->main||!s->guest||s->guest->main!=s->main||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_rc_restart_multicast_policy(&p)||!mc_same(&s->policy,&p))return 0;
 return !p.required||(s->attempted==(p.guest?3U:1U)&&
  wr_iot_restart_multicast_current(0,p.enabled)&&
  (!p.guest||wr_iot_restart_multicast_current(1,p.enabled)));
}
