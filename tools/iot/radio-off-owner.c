/* uClibc declares mkstemp used by profile headers in the XSI namespace. */
#define _XOPEN_SOURCE 700
#define _POSIX_C_SOURCE 200809L
#include <string.h>
#include <unistd.h>
#include "radio-off-owner.h"
#include "rc-physical-stop.h"
#include "rc-shutdown-admission.h"
int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner *s,const struct wr_iot_control_request *off)
{
 struct wr_iot_rc_physical_intent intent={0};int claimed;
 if(!s||!off||s->owner||s->busy||s->result||s->policy_ready||s->created||s->id[0]||
    off->request.enabled||!off->created||strnlen(off->id,sizeof(off->id))!=32||
    !wr_iot_control_id(off->id))return 0;
 s->busy=1;claimed=wr_iot_rc_physical_begin_quiesce(&intent,off);
 if(claimed==1){s->owner=getpid();memcpy(s->id,off->id,sizeof(s->id));s->created=off->created;}
 s->busy=0;return claimed==1;
}
int wr_iot_radio_off_prepare(struct wr_iot_radio_off_owner *s,int reload)
{
 struct wr_iot_radio_off_policy policy={0};int ok;
 if(!s||s->owner!=getpid()||s->busy||s->result||(reload!=0&&reload!=1))return 0;
 if(s->policy_ready)return s->policy.reload==reload;
 s->busy=1;ok=wr_iot_rc_radio_off_policy(reload,&policy);
 if(ok==1&&policy.reload==reload&&
    (policy.stored_radio==0||policy.stored_radio==1)&&
    (policy.auth_required==0||policy.auth_required==1)&&
    (!policy.auth_required||policy.stored_radio)&&
    (policy.wan==WR_WAN_NONE||policy.wan==WR_WAN_FULL_RESTART)){
  s->policy=policy;s->policy_ready=1;
 }
 s->busy=0;return s->policy_ready;
}
int wr_iot_radio_off_poll(struct wr_iot_radio_off_owner *s)
{
 int result,read;struct wr_iot_physical_stop_request released={0};
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_profile_binding binding={0};struct wr_iot_restart_profile_receipt profile={0};
#endif
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->result)return s->result;
 s->busy=1;read=wr_iot_rc_physical_off_read(s->id,s->created,&released);
 read=read==1&&released.action==WR_STOP_RELEASE&&wr_iot_physical_stop_request_valid(&released);
 if(!read&&!wr_iot_rc_physical_off_failed(s->id,s->created)){s->busy=0;return 0;}
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(read)(void)wr_iot_rc_physical_off_profile(s->id,s->created,&released,&binding,&profile);
#endif
 result=wr_iot_rc_physical_take_off(s->id,s->created);
 if(result==1&&read){s->released=released;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  s->profile_binding=binding;s->profile_receipt=profile;
#endif
 }
 if(result==1||result==-1)s->result=result;
 s->busy=0;return s->result;
}
int wr_iot_radio_off_step(struct wr_iot_radio_off_owner *s,int reload)
{
 if(!s||s->owner!=getpid()||s->busy||(reload!=0&&reload!=1))return 0;
 if(s->result)return s->result;
 if(s->policy_ready&&s->policy.reload!=reload)return 0;
 if(!wr_iot_rc_shutdown.pending&&!wr_iot_rc_physical_off_failed(s->id,s->created)&&
    !wr_iot_radio_off_prepare(s,reload))return 0;
 s->busy=1;
 if(wr_iot_rc_physical_pending())wr_iot_rc_physical_step();
 s->busy=0;
 return wr_iot_radio_off_poll(s);
}
int wr_iot_radio_off_take(struct wr_iot_radio_off_owner *s)
{
 int result;
 if(!s||s->owner!=getpid()||s->busy||!s->result)return 0;
 result=s->result;memset(s,0,sizeof(*s));return result;
}
