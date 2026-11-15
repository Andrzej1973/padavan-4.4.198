/* RC-private shutdown cleanup after exact CLOSED/rejected proof. Never restores
 * the obsolete startup profile after normal OFF's owned profile mutation. */
#include "cold-on-postshutdown.h"
static void cold_postshutdown_wipe(void *p,size_t n)
{volatile unsigned char*b=p;while(n--)*b++=0;}
static void cold_postshutdown_cleanup(void *context)
{
 struct wr_iot_cold_stop *s=context;struct wr_iot_cold_owner *p=s->parent;
 struct wr_iot_cold_admission *a=&p->admission;struct wr_iot_cold_handoff *h=s->handoff;
 size_t i;int guard=a->guard;
 wr_iot_cold_backend_parent=NULL;memset(&wr_iot_cold_backend_identity,0,sizeof(wr_iot_cold_backend_identity));
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  cold_postshutdown_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);cold_postshutdown_wipe(&a->profile,sizeof(a->profile));
 cold_postshutdown_wipe(&p->input,sizeof(p->input));cold_postshutdown_wipe(&p->generation,sizeof(p->generation));
 cold_postshutdown_wipe(&p->main,sizeof(p->main));cold_postshutdown_wipe(&p->guest,sizeof(p->guest));
 cold_postshutdown_wipe(&p->services,sizeof(p->services));cold_postshutdown_wipe(&p->multicast,sizeof(p->multicast));
 memset(a->nonce,0,sizeof(a->nonce));memset(&a->down,0,sizeof(a->down));
 a->owner=0;a->busy=0;a->guard=0;a->phase=WR_COLD_CANCELLED;
 p->owner=0;p->busy=0;p->reload=0;p->phase=WR_COLD_OWNER_IDLE;
 /* Keep live a->fence until fence_end; wipe sibling non-owning contexts. */
 cold_postshutdown_wipe(h,sizeof(*h));cold_postshutdown_wipe(s,sizeof(*s));
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_service_guard_leave(guard);
}
int wr_iot_rc_cold_postshutdown_release(struct wr_iot_cold_stop *s)
{
 struct wr_iot_cold_owner *p;struct wr_iot_cold_admission *a;
 struct wr_iot_driver_closed_result closed={0};int guest;
 if(!s||s->owner!=getpid()||s->busy||!s->parent||!s->handoff||
    (s->phase!=WR_COLD_STOP_CLOSED&&s->phase!=WR_COLD_STOP_REJECTED))return 0;
 p=s->parent;a=&p->admission;
 if(p->owner!=getpid()||p->busy||p->main.owner!=getpid()||p->main.busy||
    p->main.generation!=&p->generation||p->generation.owner!=getpid()||p->generation.busy||
    p->generation.admission!=a||!p->generation.main_may_have_started||
    p->generation.phase!=WR_COLD_GEN_VERIFIED||p->services.busy||p->multicast.busy||
    a->owner!=getpid()||a->busy!=1||a->guard!=1||a->fence.owner!=getpid()||a->fence.level!=1||
    !wr_iot_radio_profile_owned(&a->profile)||a->profile.files.count!=1||a->profile.files.pending||
    a->profile.recovering||a->profile.recovered||a->profile.removing||
    p->guest.owner!=getpid()||p->guest.busy||p->guest.main!=&p->main||
    (p->guest.phase!=WR_COLD_GUEST_DOWN_OBSERVED&&p->guest.phase!=WR_COLD_GUEST_POLICY_OFF)||
    !wr_iot_restart_guest_admin_state(&guest)||guest)return 0;
 if(s->phase==WR_COLD_STOP_CLOSED){if(!wr_iot_rc_cold_shutdown_closed(p,s->handoff,&s->off,&closed))return 0;}
 else if(!wr_iot_rc_cold_shutdown_rejected(p,s->handoff))return 0;
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,cold_postshutdown_cleanup,s)){s->busy=0;return 0;}
 return 1;
}
