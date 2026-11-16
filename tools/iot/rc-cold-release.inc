/* RC-private experimental runtime cleanup, after cold start/detach fragments.
 * Keep this stable owner through WAN/IAPP completion and checked retirement.
 * Backend shutdown remains owned by the normal controller. */
#include "rc-cold-completion.h"
static void wr_iot_cold_release_wipe(void *p,size_t n)
{volatile unsigned char *b=p;while(n--)*b++=0;}
static void wr_iot_cold_parent_cleanup(void *context)
{
 struct wr_iot_cold_parent_release *s=context;struct wr_iot_cold_release *r=s->release;
 struct wr_iot_cold_owner *parent=r->parent;struct wr_iot_cold_admission *a=&parent->admission;
 int guard=a->guard;size_t i;
 /* Infallible only after exact preflight and successful unmask. ACTIVE backend
  * owns independent startup resources and remains untouched. */
 wr_iot_rc_normal_shutdown_arm_commit();
 wr_iot_cold_detach_commit();
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  wr_iot_cold_release_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);
 wr_iot_cold_release_wipe(&a->profile,sizeof(a->profile));
 wr_iot_cold_release_wipe(&parent->input,sizeof(parent->input));
 wr_iot_cold_release_wipe(&parent->generation,sizeof(parent->generation));
 wr_iot_cold_release_wipe(&parent->main,sizeof(parent->main));
 wr_iot_cold_release_wipe(&parent->guest,sizeof(parent->guest));
 wr_iot_cold_release_wipe(&parent->services,sizeof(parent->services));
 wr_iot_cold_release_wipe(&parent->multicast,sizeof(parent->multicast));
 memset(a->nonce,0,sizeof(a->nonce));memset(&a->down,0,sizeof(a->down));
 a->owner=0;a->busy=0;a->guard=0;a->phase=WR_COLD_CANCELLED;
 parent->owner=0;parent->busy=0;parent->reload=0;parent->phase=WR_COLD_OWNER_IDLE;
 /* Preserve a->fence until fence_end clears its live token after callback. */
 wr_iot_cold_release_wipe(r->handoff,sizeof(*r->handoff));r->handoff=NULL;r->parent=NULL;
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_rc_shutdown.radio_on_owned=1;
 s->released=1;s->busy=0;
 wr_iot_service_guard_leave(guard);
}
static int wr_iot_cold_parent_release(struct wr_iot_cold_parent_release *s,
 struct wr_iot_cold_release *r)
{
 struct wr_iot_control_request request={0};int valid;
 if(!s||!r||s->busy||s->released||(s->release&&s->release!=r)||
    !wr_iot_cold_release_current(r)||!r->parent||!r->handoff)return 0;
 memcpy(request.id,r->id,sizeof(request.id));request.created=r->created;
 request.request=r->parent->generation.desired;
 valid=wr_iot_cold_detach_preflight(r->parent,&request);
 wr_iot_cold_release_wipe(&request,sizeof(request));if(!valid)return 0;
 s->release=r;s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&r->parent->admission.fence,wr_iot_cold_parent_cleanup,s)){
  s->busy=0;return 0;
 }
 return s->released;
}
