#include "mbss-poll-lifetime.h"
#include "mbss-reaper-gate.h"
#include <assert.h>
#include <stddef.h>
#define INT int
#define VOID void
#define ULONG unsigned long
#define HZ 100
struct work_struct {int unused;};
struct delayed_work {struct work_struct work;};
typedef struct {
 int wr_iot_transition_lock;
 struct wr_iot_mbss_poll_lifetime wr_iot_mbss_poll_state;
 struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;
 struct delayed_work wr_iot_mbss_poll_work;
} RTMP_ADAPTER;
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
#define to_delayed_work(p) container_of(p,struct delayed_work,work)
static int held,accept=1,polls,result=-1,cancels,bad_context,stop_during_poll,owners_idle=1;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int schedule_delayed_work(struct delayed_work *w,int delay)
{assert(w&&held&&delay>0);return accept;}
static void cancel_delayed_work_sync(struct delayed_work *w)
{assert(w&&!held);cancels++;}
static int wr_iot_os_join_context(void){return bad_context;}
static int wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad)
{assert(ad&&!held);return owners_idle?0:-1;}
static int wr_iot_mbss_recovery_poll(RTMP_ADAPTER *ad)
{
 assert(ad&&!held);polls++;
 if(stop_during_poll){
  /* Model another caller publishing stop while the poll body is unlocked. */
  wr_iot_mbss_poll_stop(&ad->wr_iot_mbss_poll_state);
  wr_iot_mbss_reaper_stop(&ad->wr_iot_mbss_reaper_gate);
 }
 return result;
}
#ifdef WR_IOT_INSTALLED_POLL
#include "wr-iot-mbss-poll-caller.inc"
#else
#include "mbss-poll-caller.inc"
#endif
/* Couple the real handoff to the real delayed caller/lifetime helpers.
 * Only owner admission and OS/backend operations remain mocked here. */
typedef void *PNET_DEV;
struct wr_iot_radio_ticket {unsigned long serial;};
static int owner_result,owner_calls,close_calls;
static const struct wr_iot_radio_ticket *original_ticket;
static int wr_iot_mbss_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev,unsigned long gen)
{assert(ad&&dev&&gen==9&&!held);owner_calls++;return owner_result;}
static int wr_iot_mbss_recovery_submit_close(RTMP_ADAPTER *ad,PNET_DEV dev,
 unsigned long gen,const struct wr_iot_radio_ticket *ticket)
{assert(ticket==original_ticket);close_calls++;return wr_iot_mbss_recovery_submit(ad,dev,gen);}
#ifdef WR_IOT_INSTALLED_POLL
#include "wr-iot-mbss-recovery-handoff.inc"
#else
#include "mbss-recovery-handoff.inc"
#endif
static void check_handoff_caller(void)
{
 int dev;struct wr_iot_radio_ticket ticket={17};
 original_ticket=&ticket;stop_during_poll=0;bad_context=0;result=0;
 for(int close=0;close<2;close++)for(int owner=-1;owner<=1;owner++)
 for(int queued=0;queued<=1;queued++){
  RTMP_ADAPTER ad={0};
  wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);
  wr_iot_mbss_reaper_gate_init(&ad.wr_iot_mbss_reaper_gate);
  owner_result=owner;accept=queued;owner_calls=close_calls=0;owners_idle=0;
  int rc=wr_iot_mbss_recovery_handoff(&ad,&dev,9,close?&ticket:0);
  assert(owner_calls==1&&close_calls==close);
  assert(rc==(owner<0?-1:owner==0&&queued?0:1));
  assert(ad.wr_iot_mbss_poll_state.unjoined==(unsigned)(owner>=0));
  assert(ad.wr_iot_mbss_poll_state.pending==(unsigned)(owner>=0&&queued));
  if(owner<0)continue;
  if(queued)wr_iot_mbss_poll_work_fn(&ad.wr_iot_mbss_poll_work.work);
  assert(ad.wr_iot_mbss_poll_state.unjoined);
  assert(wr_iot_mbss_poll_join(&ad)==-1);
  assert(ad.wr_iot_mbss_poll_state.attempts==1);
  owners_idle=1;
  assert(wr_iot_mbss_poll_join(&ad)==0);
  assert(ad.wr_iot_mbss_poll_state.attempts==0);
  assert(wr_iot_mbss_poll_stop_join(&ad)==0);
  assert(wr_iot_mbss_poll_release_ready(&ad.wr_iot_mbss_poll_state));
 }
}
int main(void){
 RTMP_ADAPTER ad={0};
 wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);
 wr_iot_mbss_reaper_gate_init(&ad.wr_iot_mbss_reaper_gate);
 assert(wr_iot_mbss_poll_schedule(&ad)==0);
 for(int i=0;i<3;i++)wr_iot_mbss_poll_work_fn(&ad.wr_iot_mbss_poll_work.work);
 assert(polls==3&&ad.wr_iot_mbss_poll_state.unjoined&&!ad.wr_iot_mbss_poll_state.pending);
 assert(wr_iot_mbss_poll_schedule(&ad)==-1);
 bad_context=1;assert(wr_iot_mbss_poll_stop_join(&ad)==-1&&!cancels);
 bad_context=0;assert(wr_iot_mbss_poll_stop_join(&ad)==0&&cancels==1);
 assert(wr_iot_mbss_poll_release_ready(&ad.wr_iot_mbss_poll_state));
 wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);
 wr_iot_mbss_reaper_gate_init(&ad.wr_iot_mbss_reaper_gate);
 accept=1;stop_during_poll=1;
 assert(wr_iot_mbss_poll_schedule(&ad)==0);
 wr_iot_mbss_poll_work_fn(&ad.wr_iot_mbss_poll_work.work);
 assert(ad.wr_iot_mbss_poll_state.stopped&&!ad.wr_iot_mbss_poll_state.pending);
 assert(ad.wr_iot_mbss_poll_state.unjoined&&!ad.wr_iot_mbss_poll_state.running);
 assert(!wr_iot_mbss_poll_release_ready(&ad.wr_iot_mbss_poll_state));
 assert(wr_iot_mbss_poll_stop_join(&ad)==0);
 assert(wr_iot_mbss_poll_release_ready(&ad.wr_iot_mbss_poll_state));
 assert(ad.wr_iot_mbss_reaper_gate.stopped&&wr_iot_mbss_poll_schedule(&ad)==-1);
 wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);
 wr_iot_mbss_reaper_gate_init(&ad.wr_iot_mbss_reaper_gate);
 accept=0;
 assert(wr_iot_mbss_poll_schedule(&ad)==-1);
 assert(ad.wr_iot_mbss_poll_state.unjoined);
 assert(wr_iot_mbss_poll_schedule(&ad)==-1);
 assert(wr_iot_mbss_poll_stop_join(&ad)==0);
 assert(wr_iot_mbss_poll_release_ready(&ad.wr_iot_mbss_poll_state));
 stop_during_poll=0;accept=1;
 wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);
 assert(wr_iot_mbss_poll_schedule(&ad)==0);
 result=0;wr_iot_mbss_poll_work_fn(&ad.wr_iot_mbss_poll_work.work);
 assert(wr_iot_mbss_poll_join(&ad)==0&&ad.wr_iot_mbss_poll_state.attempts==0);
 assert(wr_iot_mbss_poll_schedule(&ad)==0);
 owners_idle=0;
 assert(wr_iot_mbss_poll_join(&ad)==-1&&ad.wr_iot_mbss_poll_state.attempts==1);
 assert(!ad.wr_iot_mbss_poll_state.joining);
 check_handoff_caller();
 return 0;
}
