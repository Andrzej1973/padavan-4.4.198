/* Uncomposed RC-private disabled cold cleanup after rc-cold-start.inc.
 * Only IDLE/INITIAL_OFF backend with no live startup/stop/rebind is eligible. */
#include "rc-cold-disabled-completion.h"
static int wr_iot_cold_disabled_backend_idle(void)
{
 return !wr_iot_cold_backend_parent&&!rebind.owner&&!backend.busy&&
  !backend.start.owner&&!backend.stop.owner&&!backend.start.admission.snapshot.active&&
  !backend.start.admission.snapshot.token&&
  ((!backend.owner&&backend.phase==WR_IOT_OWNER_IDLE)||
   (backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF));
}
static void wr_iot_cold_disabled_wipe(void *data,size_t n)
{volatile unsigned char *p=data;while(n--)*p++=0;}
static void wr_iot_cold_disabled_parent_cleanup(void *context)
{
 struct wr_iot_cold_disabled_parent_release *s=context;
 struct wr_iot_cold_disabled_release *r=s->release;struct wr_iot_cold_owner *p=r->parent;
 struct wr_iot_cold_admission *a=&p->admission;size_t i;int guard=a->guard;
 /* Copy only the inert nonsecret observation, never an owned controller. */
 backend.initial_off=r->disabled->idle;backend.owner=getpid();backend.phase=WR_IOT_OWNER_INITIAL_OFF;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  wr_iot_cold_disabled_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);wr_iot_cold_disabled_wipe(&a->profile,sizeof(a->profile));
 wr_iot_cold_disabled_wipe(&p->input,sizeof(p->input));
 wr_iot_cold_disabled_wipe(&p->generation,sizeof(p->generation));
 wr_iot_cold_disabled_wipe(&p->main,sizeof(p->main));wr_iot_cold_disabled_wipe(&p->guest,sizeof(p->guest));
 wr_iot_cold_disabled_wipe(&p->services,sizeof(p->services));wr_iot_cold_disabled_wipe(&p->multicast,sizeof(p->multicast));
 memset(a->nonce,0,sizeof(a->nonce));memset(&a->down,0,sizeof(a->down));
 a->owner=0;a->busy=0;a->guard=0;a->phase=WR_COLD_CANCELLED;
 p->owner=0;p->busy=0;p->reload=0;p->phase=WR_COLD_OWNER_IDLE;
 /* Leave a->fence untouched for fence_end's final token release. */
 wr_iot_cold_disabled_wipe(r->disabled,sizeof(*r->disabled));r->disabled=NULL;r->parent=NULL;
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_rc_shutdown.radio_on_owned=1;
 s->released=1;s->busy=0;wr_iot_service_guard_leave(guard);
}
static int wr_iot_cold_disabled_parent_release(struct wr_iot_cold_disabled_parent_release *s,
 struct wr_iot_cold_disabled_release *r)
{
 if(!s||!r||s->busy||s->released||(s->release&&s->release!=r)||
    !wr_iot_cold_disabled_backend_idle()||!wr_iot_cold_disabled_release_current(r))return 0;
 s->release=r;s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&r->parent->admission.fence,wr_iot_cold_disabled_parent_cleanup,s)){
  s->busy=0;return 0;
 }
 return s->released;
}
