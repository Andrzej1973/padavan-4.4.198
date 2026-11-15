#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-root-recovery.h"
#include "cold-on-recovery.h"
#include "rc-shutdown-admission.h"
/* Private root recovery before any attempted Main UP. The exact child owns
 * file restore/DOWN proof and signal-fenced resource release. */
int wr_iot_cold_root_preup_recover(struct wr_iot_cold_root *s)
{
 struct wr_iot_cold_owner *p;struct wr_iot_cold_generation *g;
 volatile unsigned char *bytes;size_t n;int finished=0;
 if(!s||s->owner!=getpid()||s->busy||
    (s->phase!=WR_COLD_ROOT_PREPARE&&s->phase!=WR_COLD_ROOT_RETAINED)||
    s->handoff.owner||s->handoff.attempted||s->release.owner||s->released.release||
    s->terminal.owner||s->disabled.owner||s->disabled_release.owner||
    s->disabled_released.release||s->disabled_terminal.owner||s->stop.owner||s->stop.busy||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_shutdown.radio_on_owned)return 0;
 p=&s->parent;g=&p->generation;
 if(p->owner!=getpid()||p->busy||p->main.owner||p->main.busy||
    p->guest.owner||p->services.owner||p->multicast.owner||g->main_may_have_started||g->busy||
    p->admission.owner!=getpid()||
    (g->owner&&(g->owner!=getpid()||g->admission!=&p->admission))||
    (!g->owner&&(g->admission||p->admission.busy)))return 0;
 s->busy=1;s->phase=WR_COLD_ROOT_RETAINED;p->phase=WR_COLD_OWNER_RETAINED;
 /* Cancellation is irreversible, even if unmask/restore refuses. A request
  * captured before generation must not survive pending signal replay or be
  * submitted later with an emptied/changed credential set. */
 bytes=(volatile unsigned char *)&p->input.request;n=sizeof(p->input.request);
 while(n--)*bytes++=0;
 if(!g->owner)finished=wr_iot_cold_admission_cancel(&p->admission);
 else if(wr_iot_cold_preup_recover(g)==-1)finished=wr_iot_cold_preup_finish(g);
 if(!finished){s->busy=0;return 0;}
 /* Child release has already wiped credentials and guard before normal
  * pending shutdown replay. Only local, non-owning root metadata remains. */
 bytes=(volatile unsigned char *)s;n=sizeof(*s);while(n--)*bytes++=0;
 return 1;
}
