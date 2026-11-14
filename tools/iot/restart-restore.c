#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "restart-restore.h"
#include "rc-shutdown-admission.h"
#include "rc-backend.h"
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore *s,const unsigned char *id)
{
 unsigned i,nonzero=0;
 if(!s||!id||s->owner||s->busy||s->phase!=WR_RESTORE_IDLE||
    s->generation.owner||s->main.owner||s->guest.owner||s->services.owner||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 for(i=0;i<16;i++)nonzero|=id[i];
 if(!nonzero)return 0;
 s->owner=getpid();s->busy=1;memcpy(s->open_id,id,16);
 s->phase=WR_RESTORE_PROFILE;
 if(!wr_iot_restart_generation_begin(&s->generation))s->phase=WR_RESTORE_RETAINED;
 s->busy=0;return s->phase==WR_RESTORE_PROFILE;
}
int wr_iot_restart_restore_step(struct wr_iot_restart_restore *s)
{
 int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)return 0;
 s->busy=1;
 if(wr_iot_rc_shutdown.pending){
  /* Guest owns its submitted UP and must retain/observe its DOWN recovery.
   * Main/profile ownership remains fenced; no broad cleanup is inferred. */
  if(!s->generation.main_may_have_started&&s->generation.owner==getpid()){
   /* Before Main submission, use the existing owned profile rollback. Never
    * restore after a possible UP, even if later administrative DOWN is seen. */
   (void)wr_iot_restart_generation_abort(&s->generation);
   (void)wr_iot_restart_generation_step(&s->generation);
  }
  if(s->guest.owner)(void)wr_iot_restart_guest_step(&s->guest);
  goto done;
 }
 switch(s->phase){
 case WR_RESTORE_PROFILE:
  if(wr_iot_restart_generation_step(&s->generation))s->phase=WR_RESTORE_MAIN_START;
  break;
 case WR_RESTORE_MAIN_START:
  /* Never repeat Main begin, even on uncertain transport return. */
  s->phase=WR_RESTORE_MAIN_WAIT;
  (void)wr_iot_restart_main_begin(&s->main,&s->generation,s->open_id);
  if(!s->main.owner)s->phase=WR_RESTORE_RETAINED;
  break;
 case WR_RESTORE_MAIN_WAIT:
  if(wr_iot_restart_main_lan_step(&s->main))s->phase=WR_RESTORE_GUEST_BEGIN;
  break;
 case WR_RESTORE_GUEST_BEGIN:
  if(wr_iot_restart_guest_begin(&s->guest,&s->main))s->phase=WR_RESTORE_GUEST_WAIT;
  break;
 case WR_RESTORE_GUEST_WAIT:
  if(wr_iot_restart_guest_step(&s->guest))s->phase=WR_RESTORE_SERVICE_BEGIN;
  break;
 case WR_RESTORE_SERVICE_BEGIN:
  if(!wr_iot_restart_guest_step(&s->guest))break;
  if(wr_iot_restart_services_begin(&s->services,&s->main))s->phase=WR_RESTORE_SERVICE_WAIT;
  break;
 case WR_RESTORE_SERVICE_WAIT:
 case WR_RESTORE_PREPARED:
  if(!wr_iot_restart_guest_step(&s->guest))break;
  if(wr_iot_restart_services_step(&s->services)){
   s->phase=WR_RESTORE_PREPARED;ok=1;
  }
  break;
 default:break;
 }
 done:s->busy=0;return ok;
}

int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *request)
{
 unsigned i;unsigned char nonce[16];int admitted;
 if(!s||!request||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_PREPARED||
    !request->created||request->request.enabled!=1||
    !memchr(request->id,0,sizeof(request->id))||!wr_iot_control_id(request->id))return 0;
 for(i=0;i<16;i++){
  unsigned char a=request->id[2*i],b=request->id[2*i+1];
  nonce[i]=(unsigned char)(((a<='9'?a-'0':a-'a'+10)<<4)|(b<='9'?b-'0':b-'a'+10));
 }
 if(memcmp(nonce,s->open_id,sizeof(nonce)))return 0;
#define SAME(f) if(!memchr(request->request.f,0,sizeof(request->request.f))||strcmp(request->request.f,s->generation.origin.desired.f))return 0;
 SAME(ssid) SAME(password) SAME(gateway) SAME(mask) SAME(first) SAME(last)
#undef SAME
 if(!wr_iot_restart_restore_step(s))return 0;
 s->busy=1;s->phase=WR_RESTORE_HANDOFF;s->handoff_created=request->created;
 /* Backend owns its new runner at final address; never copy it here. A
  * refusal may retain partial admission, so never retry begin automatically. */
 admitted=wr_iot_rc_rebind_begin(request,&s->generation.origin.physical);
 s->busy=0;return admitted;
}

int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore *s)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request request={0};unsigned i;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    !s->handoff_created||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    s->main.generation!=&s->generation||s->main.owner!=getpid()||
    !wr_iot_restart_generation_origin_current(&s->generation))return 0;
 s->busy=1;
 for(i=0;i<16;i++){request.id[2*i]=hex[s->open_id[i]>>4];request.id[2*i+1]=hex[s->open_id[i]&15];}
 request.created=s->handoff_created;request.request=s->generation.origin.desired;
 if(wr_iot_rc_rebind_active_current(&request,&s->generation.origin.physical,&s->main.identity)&&
    wr_iot_restart_generation_origin_current(&s->generation)&&!wr_iot_rc_shutdown.pending)ok=1;
 /* Copied envelope contains credentials; never retain another copy or log it. */
 {volatile unsigned char *p=(volatile unsigned char *)&request;size_t n=sizeof(request);while(n--)*p++=0;}
 s->busy=0;return ok;
}
