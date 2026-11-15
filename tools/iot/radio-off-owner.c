#include <string.h>
#include <unistd.h>
#include "radio-off-owner.h"
#include "rc-physical-stop.h"
int wr_iot_radio_off_begin(struct wr_iot_radio_off_owner *s,const struct wr_iot_control_request *off)
{
 struct wr_iot_rc_physical_intent intent={0};int claimed;
 if(!s||!off||s->owner||s->busy||s->result||s->created||s->id[0]||
    off->request.enabled||!off->created||strnlen(off->id,sizeof(off->id))!=32||
    !wr_iot_control_id(off->id))return 0;
 s->busy=1;claimed=wr_iot_rc_physical_begin_quiesce(&intent,off);
 if(claimed==1){s->owner=getpid();memcpy(s->id,off->id,sizeof(s->id));s->created=off->created;}
 s->busy=0;return claimed==1;
}
int wr_iot_radio_off_poll(struct wr_iot_radio_off_owner *s)
{
 int result;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->result)return s->result;
 s->busy=1;result=wr_iot_rc_physical_take_off(s->id,s->created);
 if(result==1||result==-1)s->result=result;
 s->busy=0;return s->result;
}
int wr_iot_radio_off_take(struct wr_iot_radio_off_owner *s)
{
 int result;
 if(!s||s->owner!=getpid()||s->busy||!s->result)return 0;
 result=s->result;memset(s,0,sizeof(*s));return result;
}
