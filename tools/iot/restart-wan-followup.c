#include <unistd.h>
#include "restart-wan-followup.h"
#include "rc-shutdown-admission.h"
int wr_iot_wan_followup_capture(struct wr_iot_wan_followup_state*s,int radio_on)
{
 enum wr_iot_wan_followup plan;
 if(!s||s->owner||s->attempted||s->returned||!wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||!wr_iot_rc_restart_wan_plan(radio_on,&plan)||
    plan<WR_WAN_NONE||plan>WR_WAN_RECONNECT)return 0;
 s->owner=getpid();s->radio_on=radio_on;s->plan=plan;return 1;
}
int wr_iot_wan_followup_step(struct wr_iot_wan_followup_state*s)
{
 if(!s||s->owner!=getpid()||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 if(s->attempted)return s->returned;
 if(s->plan<WR_WAN_NONE||s->plan>WR_WAN_RECONNECT)return 0;
 if(!wr_iot_rc_restart_wan_current(s->radio_on,s->plan))return 0;
 s->attempted=1;
 if(s->plan!=WR_WAN_NONE)wr_iot_rc_restart_wan_submit(s->plan);
 s->returned=1;return 1;
}
