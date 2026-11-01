#include "mcu-sender-owner.h"
#include <assert.h>
#include <stdlib.h>
typedef unsigned long ULONG;
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait,counters;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} RTMP_ADAPTER;
struct cmd_msg {RTMP_ADAPTER *ad;};
static int held,fail_alloc,allocs,wakes,retired;
static RTMP_ADAPTER *retire_target;
static void unlock_end(void){
 if(retire_target&&!retire_target->wr_iot_mcu_sender_owner.messages){
  assert(wr_iot_mcu_sender_release_claim(&retire_target->wr_iot_mcu_sender_owner));
  free(retire_target);retire_target=0;retired++;
 }
}
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;unlock_end();}while(0)
static void wake_up_all(int *w){(void)w;assert(held);wakes++;}
static struct cmd_msg *wr_iot_mcu_alloc_body(RTMP_ADAPTER *a,unsigned int length){
 assert(!held&&a->wr_iot_mcu_sender_owner.messages==1);(void)length;allocs++;
 if(fail_alloc)return 0;
 struct cmd_msg *m=malloc(sizeof(*m));assert(m);m->ad=a;return m;
}
#include "mcu-message-lifetime.inc"
static void destroy(struct cmd_msg *m){RTMP_ADAPTER *a=m->ad;free(m);a->counters++;wr_iot_mcu_message_drop(a);}
int main(void){RTMP_ADAPTER a={0};struct cmd_msg *m;
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);fail_alloc=1;
 assert(!AndesAllocCmdMsg(&a,8)&&!a.wr_iot_mcu_sender_owner.messages&&wakes==1);
 fail_alloc=0;assert(wr_iot_mcu_sender_close(&a.wr_iot_mcu_sender_owner,1));
 m=AndesAllocCmdMsg(&a,8);assert(m);assert(!wr_iot_mcu_sender_release_claim(&a.wr_iot_mcu_sender_owner));
 destroy(m);assert(a.counters==1&&!a.wr_iot_mcu_sender_owner.messages);
 assert(wr_iot_mcu_sender_release_claim(&a.wr_iot_mcu_sender_owner));
 int old=allocs;assert(!AndesAllocCmdMsg(&a,8)&&allocs==old);
 RTMP_ADAPTER *heap=calloc(1,sizeof(*heap));assert(heap);wr_iot_mcu_sender_init(&heap->wr_iot_mcu_sender_owner);
 assert(wr_iot_mcu_sender_close(&heap->wr_iot_mcu_sender_owner,2));
 m=AndesAllocCmdMsg(heap,8);assert(m);retire_target=heap;destroy(m);
 assert(retired==1&&!retire_target&&!held);assert(!AndesAllocCmdMsg(0,8));return 0;}
