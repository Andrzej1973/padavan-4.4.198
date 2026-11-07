#include "timer-task-owner.h"
#include <assert.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define READ_ONCE(x) (x)
#define RTMP_TASK_CAN_DO_INSERT 3
typedef int BOOLEAN;typedef void VOID;typedef unsigned long ULONG;
typedef struct timer {int TimerObj,Valid,wr_iot_retiring;void *pAd;} RALINK_TIMER_STRUCT;
typedef struct node {RALINK_TIMER_STRUCT *pRaTimer;struct node *pNext;} RTMP_TIMER_TASK_ENTRY;
typedef struct {int TimerQLock,timerTask,wr_iot_timer_drain_wait;
struct {int status;RTMP_TIMER_TASK_ENTRY *pQHead,*pQTail,*pQPollFreeList;} TimerQ;
struct wr_iot_timer_task_owner wr_iot_timer_owner;} RTMP_ADAPTER;
static int held,context_bad,self_task,syncs,sync_fail,waits,complete_task,pending;
static int late_queue,late_owner;
static RTMP_ADAPTER adapter;static RALINK_TIMER_STRUCT timer,other;
static RTMP_TIMER_TASK_ENTRY nodes[5];
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define wr_iot_os_join_context() (context_bad)
#define wr_iot_os_timer_task_current(t) ((void)(t),self_task)
static void wr_iot_timer_fence(RALINK_TIMER_STRUCT *t){assert(!held);t->wr_iot_retiring=1;}
static int sync_timer(int *native){(void)native;assert(!held);syncs++;if(syncs==sync_fail)return -1;pending=0;
#ifdef RTMP_TIMER_TASK_SUPPORT
 if(syncs==2&&late_queue){
  RTMP_TIMER_TASK_ENTRY *n=adapter.TimerQ.pQPollFreeList;assert(n);
  adapter.TimerQ.pQPollFreeList=n->pNext;n->pNext=NULL;n->pRaTimer=&timer;
  if(adapter.TimerQ.pQTail)adapter.TimerQ.pQTail->pNext=n;else adapter.TimerQ.pQHead=n;
  adapter.TimerQ.pQTail=n;
 }
 if(syncs==2&&late_owner)assert(wr_iot_timer_task_owner_begin(&adapter.wr_iot_timer_owner,&timer));
#endif
 return 0;}
#define wr_iot_os_sync_timer(t) sync_timer(t)
#ifdef RTMP_TIMER_TASK_SUPPORT
static void wait_hook(void){
 assert(!held);waits++;
 if(complete_task&&adapter.wr_iot_timer_owner.running){
  assert(wr_iot_timer_task_owner_end(&adapter.wr_iot_timer_owner,&timer,adapter.wr_iot_timer_owner.serial));
  pending=1; /* admitted task rearms after the first OS sync */
 }
}
#define msecs_to_jiffies(t) (t)
#define wait_event_timeout(w,c,t) ((void)(w),(void)(t),wait_hook(),(c)?1:0)
#endif
#include "wr-iot-timer-checked-join.inc"
static void setup(void){
 memset(&adapter,0,sizeof adapter);timer=(RALINK_TIMER_STRUCT){0,1,0,&adapter};
 other=(RALINK_TIMER_STRUCT){0,1,0,&adapter};held=context_bad=self_task=syncs=waits=complete_task=pending=late_queue=late_owner=0;sync_fail=-1;
 adapter.TimerQ.status=RTMP_TASK_CAN_DO_INSERT;wr_iot_timer_task_owner_init(&adapter.wr_iot_timer_owner);
 for(int i=0;i<5;i++)nodes[i]=(RTMP_TIMER_TASK_ENTRY){i==1||i==4?&other:&timer,i==4?NULL:&nodes[i+1]};
 adapter.TimerQ.pQHead=&nodes[0];adapter.TimerQ.pQTail=&nodes[4];
}
int main(void){
 setup();context_bad=1;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&!syncs&&!timer.wr_iot_retiring);
 setup();assert(!wr_iot_timer_join_checked(&adapter,&timer,0)&&!syncs);
 assert(!wr_iot_timer_join_checked(&adapter,&timer,5001)&&!syncs);
 setup();sync_fail=1;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==1&&timer.wr_iot_retiring);
 setup();sync_fail=2;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==2);
 setup();assert(wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==2&&!held&&timer.Valid&&timer.wr_iot_retiring);
#ifdef RTMP_TIMER_TASK_SUPPORT
 assert(adapter.TimerQ.pQHead==&nodes[1]&&nodes[1].pNext==&nodes[4]&&adapter.TimerQ.pQTail==&nodes[4]);
 {int n=0;for(RTMP_TIMER_TASK_ENTRY *p=adapter.TimerQ.pQPollFreeList;p;p=p->pNext)n++;assert(n==3);}
 setup();self_task=1;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&!syncs&&!timer.wr_iot_retiring);
 setup();self_task=-1;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&!syncs);
 setup();adapter.TimerQ.status=0;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&!syncs);
 setup();assert(wr_iot_timer_task_owner_begin(&adapter.wr_iot_timer_owner,&timer));
 assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==1&&waits==1&&adapter.wr_iot_timer_owner.running==&timer);
 setup();assert(wr_iot_timer_task_owner_begin(&adapter.wr_iot_timer_owner,&timer));complete_task=1;
 assert(wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==2&&waits==1&&!pending&&!adapter.wr_iot_timer_owner.running);
 setup();adapter.wr_iot_timer_owner.poisoned=1;
 assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==1&&waits==1);
 setup();for(int i=0;i<5;i++)nodes[i].pRaTimer=&timer;
 assert(wr_iot_timer_join_checked(&adapter,&timer,100)&&!adapter.TimerQ.pQHead&&!adapter.TimerQ.pQTail);
 setup();late_queue=1;assert(wr_iot_timer_join_checked(&adapter,&timer,100));
 assert(adapter.TimerQ.pQHead==&nodes[1]&&nodes[1].pNext==&nodes[4]&&adapter.TimerQ.pQTail==&nodes[4]);
 setup();late_owner=1;assert(!wr_iot_timer_join_checked(&adapter,&timer,100)&&syncs==2&&adapter.wr_iot_timer_owner.running==&timer);
#endif
return 0;}
