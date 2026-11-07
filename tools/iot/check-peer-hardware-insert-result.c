#include <assert.h>
#include <stddef.h>
#define TRUE 1
#define FALSE 0
#define HIF_MT 1
#define WR_IOT_WCID_APPLIED 0
typedef int INT;typedef unsigned long ULONG;
struct entry {int wcid;unsigned char Addr[6];int kind;int EnqueueStartForPSKTimer,RetryTimer,SAQueryTimer,SAQueryConfirmTimer,EapReqIdRetryTimer;};
struct tr {int enq_cap,deq_cap,wr_iot_setup_observed,wr_iot_setup_result;};
struct adapter {int MacTabLock,irq_lock;struct {int hif_type;} chipCap;};
static int mac,irq,status,checked,legacy,published,fenced;
#define wr_iot_timer_fence(t) do{(void)(t);assert(mac&&!irq);fenced++;}while(0)
#define IS_ENTRY_CLIENT(p) ((p)->kind==1)
#define IS_ENTRY_APCLI(p) ((p)->kind==2)
#define wr_iot_update_rx_wcid_checked(a,w,p) ((void)(a),(void)(w),(void)(p),checked++,status)
#define RTMP_STA_ENTRY_ADD(a,p) do{(void)(a);(void)(p);legacy++;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(mac&&!irq);irq=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(mac&&irq);irq=0;}while(0)
#define WRITE_ONCE(x,v) do{assert(mac&&irq);(x)=(v);}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(mac&&!irq);mac=0;}while(0)
#if defined(TEST_TIMER_FENCE) && defined(MT_MAC)
static int expected_fences(int kind){
 int n=1;
#ifdef CONFIG_AP_SUPPORT
 if(kind==1){n++;
#ifdef DOT11W_PMF_SUPPORT
 n+=2;
#endif
#ifdef WSC_INCLUDED
 n++;
#endif
 }
#ifdef APCLI_SUPPORT
 if(kind==2){n++;
#if defined(APCLI_DOT11W_PMF_SUPPORT) && defined(DOT11W_PMF_SUPPORT)
 n+=2;
#endif
 }
#endif
#else
 (void)kind;
#endif
 return n;
}
#endif
static struct entry *insert(struct adapter *pAd,struct entry *pEntry,struct tr *tr_entry)
{
 (void)pAd;
#include "wr-iot-peer-hardware-insert-result.inc"
 published++;tr_entry->enq_cap=tr_entry->deq_cap=TRUE;return pEntry;
}
int main(void)
{
 struct adapter a={0};struct entry e={.wcid=1,.Addr={1,2,3,4,5,6},.kind=1};struct tr t;
 a.chipCap.hif_type=HIF_MT;
 for(status=-2;status<=0;status++){
  t=(struct tr){0};mac=1;irq=checked=legacy=published=fenced=0;
#ifdef MT_MAC
  assert((insert(&a,&e,&t)!=NULL)==(status==0));
  assert(checked==1&&!legacy&&t.wr_iot_setup_observed&&t.wr_iot_setup_result==status);
  assert(published==(status==0)&&t.enq_cap==(status==0)&&t.deq_cap==(status==0)&&mac==(status==0));
  assert(e.kind==1); /* failure must not make WCID reusable */
#ifdef TEST_TIMER_FENCE
  assert(fenced==(status==0?0:expected_fences(e.kind)));
#endif
#else
  assert(insert(&a,&e,&t)==&e&&legacy==1&&!checked&&published==1);
#endif
 }
 a.chipCap.hif_type=0;t=(struct tr){0};mac=1;irq=checked=legacy=published=0;
 assert(insert(&a,&e,&t)==&e&&legacy==1&&!checked&&published==1&&!t.wr_iot_setup_observed);
#if defined(TEST_TIMER_FENCE) && defined(MT_MAC)
 a.chipCap.hif_type=HIF_MT;status=-1;
 for(int kind=1;kind<=3;kind++){
  e.kind=kind;t=(struct tr){0};mac=1;irq=checked=legacy=published=fenced=0;
  assert(!insert(&a,&e,&t)&&!mac&&!published&&fenced==expected_fences(kind));
 }
#endif
 return 0;
}
