#include "mcu-sender-owner.h"
#include <assert.h>
typedef unsigned long ULONG;typedef int INT;
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} RTMP_ADAPTER;
static int held,atomic_context,irq_off,finish_on_wait,waits;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define msecs_to_jiffies(x) (x)
static void before_wait(RTMP_ADAPTER *a){assert(!held);waits++;if(finish_on_wait)assert(wr_iot_mcu_sender_leave(&a->wr_iot_mcu_sender_owner));}
#define wait_event_timeout(q,condition,timeout) ((void)(q),assert((timeout)==5000),before_wait(ad),(condition)?1:0)
#include "mcu-sender-drain.inc"
int main(void){RTMP_ADAPTER a={0};
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);
 atomic_context=1;assert(wr_iot_mcu_sender_close_drain(&a,1)==-1&&!a.wr_iot_mcu_sender_owner.closed);
 atomic_context=0;irq_off=1;assert(wr_iot_mcu_sender_close_drain(&a,1)==-1);
 irq_off=0;assert(wr_iot_mcu_sender_enter(&a.wr_iot_mcu_sender_owner));
 assert(wr_iot_mcu_sender_close_drain(&a,1)==-1);assert(a.wr_iot_mcu_sender_owner.closed);
 assert(!wr_iot_mcu_sender_enter(&a.wr_iot_mcu_sender_owner));
 int old_waits=waits;assert(wr_iot_mcu_sender_close_drain(&a,2)==-1&&waits==old_waits);
 finish_on_wait=1;assert(wr_iot_mcu_sender_close_drain(&a,1)==0);
 finish_on_wait=0;assert(wr_iot_mcu_sender_off_begin(&a.wr_iot_mcu_sender_owner,1));
 assert(wr_iot_mcu_sender_close_drain(&a,1)==-1);
 assert(wr_iot_mcu_sender_off_finish(&a.wr_iot_mcu_sender_owner,1,0));
 assert(wr_iot_mcu_sender_close_drain(&a,1)==-1);
 assert(wr_iot_mcu_sender_close_drain(0,1)==-1);assert(!held);
 return 0;}
