#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>
typedef unsigned long ULONG;
typedef int INT;
struct adapter {
 struct wr_iot_radio_transition wr_iot_transition;
 int wr_iot_transition_lock,wr_iot_ticket_wait;
};
typedef struct adapter *PRTMP_ADAPTER;
static int held,complete_on_wait,waits;
static struct wr_iot_radio_ticket pending;
static PRTMP_ADAPTER current;
#define RTMP_IRQ_LOCK(lock,flags) do {(void)(lock);(void)(flags);assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do {(void)(lock);(void)(flags);assert(held);held=0;}while(0)
static void mock_wait(int *queue,unsigned long timeout)
{
 assert(queue==&current->wr_iot_ticket_wait&&!held&&timeout);
 waits++;
 if(complete_on_wait){
  complete_on_wait=0;
  assert(wr_iot_radio_finish_unverified(&current->wr_iot_transition,&pending));
 }
}
#define wait_event_timeout(queue,condition,timeout) \
 (mock_wait(&(queue),(timeout)),(condition))
#include "radio-ticket-wait.inc"
int main(void)
{
 struct adapter a={0};
 current=&a;
 wr_iot_radio_transition_init(&a.wr_iot_transition);
 a.wr_iot_transition.phase=WR_RADIO_READY;
 a.wr_iot_transition.main_ready=1;
 assert(wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,
                           WR_RADIO_BSS_OPEN,&pending));
 assert(wr_iot_wait_ticket_retired(&a,pending.serial,0)==-1&&!waits);
 complete_on_wait=1;
 assert(wr_iot_wait_ticket_retired(&a,pending.serial,5)==0&&waits==1&&!held);
 assert(wr_iot_wait_ticket_retired(&a,pending.serial,0)==0&&waits==1);
 assert(wr_iot_wait_ticket_retired(&a,0,5)==-1&&waits==1);
 assert(wr_iot_wait_ticket_retired(0,pending.serial,5)==-1&&waits==1);
 assert(wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,
                           WR_RADIO_BSS_CLOSE,&pending));
 assert(wr_iot_wait_ticket_retired(&a,pending.serial,5)==-1&&waits==2);
 puts("PASS ticket wait: immediate, bounded completion, timeout and invalid input");
 return 0;
}
