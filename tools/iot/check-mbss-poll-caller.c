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
static int held,accept=1,polls,result=-1,cancels,bad_context;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int schedule_delayed_work(struct delayed_work *w,int delay)
{assert(w&&held&&delay>0);return accept;}
static void cancel_delayed_work_sync(struct delayed_work *w)
{assert(w&&!held);cancels++;}
static int wr_iot_os_join_context(void){return bad_context;}
static int wr_iot_mbss_recovery_poll(RTMP_ADAPTER *ad)
{assert(ad&&!held);polls++;return result;}
#include "mbss-poll-caller.inc"
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
 assert(ad.wr_iot_mbss_reaper_gate.stopped&&wr_iot_mbss_poll_schedule(&ad)==-1);
 return 0;
}
