#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-handoff.h"
#include "radio-on-aux.h"
#include "control-channel.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static int on_parent_chain(struct wr_iot_on_restore *s)
{
 return s->main.owner==getpid()&&s->main.generation==&s->generation&&
  s->guest.owner==getpid()&&s->guest.main==&s->main&&
  s->services.owner==getpid()&&s->services.guest==&s->guest&&
  s->multicast.owner==getpid()&&s->multicast.main==&s->main&&s->multicast.guest==&s->guest;
}
int wr_iot_on_restore_handoff(struct wr_iot_on_restore *s,const struct wr_iot_control_request *r)
{
 unsigned i;unsigned char nonce[16];int admitted;
 if(!s||!r||s->owner!=getpid()||s->busy||s->phase!=WR_ON_RESTORE_PREPARED||s->handoff_created||
    !r->created||r->request.enabled!=1||!memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    !on_parent_chain(s))return 0;
 for(i=0;i<16;i++){
  unsigned char a=r->id[2*i],b=r->id[2*i+1];
  nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
 }
 if(memcmp(nonce,s->open_id,sizeof(nonce)))return 0;
#define SAME(f) if(!memchr(r->request.f,0,sizeof(r->request.f))||strcmp(r->request.f,s->generation.desired.f))return 0;
 SAME(ssid) SAME(password) SAME(gateway) SAME(mask) SAME(first) SAME(last)
#undef SAME
 if(!wr_iot_on_restore_step(s))return 0;
 s->busy=1;s->phase=WR_ON_RESTORE_HANDOFF;s->handoff_created=r->created;
 admitted=wr_iot_rc_rebind_begin(r,&s->generation.admission->released);
 s->busy=0;return admitted;
}
static int on_rebind_observe(struct wr_iot_on_restore *s,int advance)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request r={0};unsigned i;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||
    (s->phase!=WR_ON_RESTORE_HANDOFF&&(advance||s->phase!=WR_ON_RESTORE_RELEASING))||!s->handoff_created||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!on_parent_chain(s)||
    !wr_iot_on_generation_origin_current(&s->generation)||!wr_iot_on_aux_down_current())return 0;
 s->busy=1;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.request=s->generation.desired;
 if(advance)(void)wr_iot_activation_continue(r.id,r.created);
 if(wr_iot_rc_rebind_active_current(&r,&s->generation.admission->released,&s->main.identity)&&
    wr_iot_on_generation_origin_current(&s->generation)&&wr_iot_on_aux_down_current()&&
    wr_iot_on_multicast_observed(&s->multicast)&&!wr_iot_rc_shutdown.pending)ok=1;
 {volatile unsigned char *p=(volatile unsigned char *)&r;size_t n=sizeof(r);while(n--)*p++=0;}
 s->busy=0;return ok;
}

int wr_iot_on_rebind_step(struct wr_iot_on_restore *s)
{return on_rebind_observe(s,1);}
int wr_iot_on_rebind_current(struct wr_iot_on_restore *s)
{return on_rebind_observe(s,0);}
