#ifndef WR_IOT_CHECK_MULTICAST_OWNER_ACTOR_H
#define WR_IOT_CHECK_MULTICAST_OWNER_ACTOR_H
/* Component actor for fixtures whose scope excludes multicast policy/IO. */
#include <unistd.h>
#include "restart-multicast-controller.h"
int wr_iot_restart_multicast_begin(struct wr_iot_multicast*s,struct wr_iot_restart_main*m,struct wr_iot_restart_guest*g)
{s->owner=getpid();s->main=m;s->guest=g;s->phase=WR_MC_READY;return 1;}
int wr_iot_restart_multicast_step(struct wr_iot_multicast*s)
{return s->owner==getpid()&&!s->busy&&s->phase==WR_MC_READY;}
int wr_iot_restart_multicast_observed(struct wr_iot_multicast*s)
{return s->owner==getpid()&&!s->busy&&s->phase==WR_MC_READY;}
#endif
