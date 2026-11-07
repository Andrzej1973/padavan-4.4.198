#include "mcu-sender-owner.h"
#include <assert.h>
typedef int INT;typedef unsigned long ULONG;
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
typedef struct {int wr_iot_mcu_sender_lock;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} RTMP_ADAPTER;
static int held;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#include "mcu-sender-release.inc"
int main(void){RTMP_ADAPTER a={0};struct wr_iot_mcu_sender_owner *s=&a.wr_iot_mcu_sender_owner;
 wr_iot_mcu_sender_init(s);assert(wr_iot_mcu_sender_enter(s));assert(wr_iot_mcu_message_enter(s));
 assert(wr_iot_mcu_sender_release_begin(&a)==-1&&s->closed&&!s->release_claimed);
 assert(!wr_iot_mcu_sender_enter(s));assert(wr_iot_mcu_sender_leave(s));
 assert(wr_iot_mcu_sender_release_begin(&a)==-1);assert(wr_iot_mcu_message_leave(s));
 assert(wr_iot_mcu_sender_release_begin(&a)==0);assert(wr_iot_mcu_sender_release_begin(&a)==0);
 assert(!wr_iot_mcu_message_enter(s)&&!wr_iot_mcu_sender_off_begin(s,~0UL));
 wr_iot_mcu_sender_init(s);assert(wr_iot_mcu_sender_close(s,7));assert(wr_iot_mcu_sender_off_begin(s,7));
 assert(wr_iot_mcu_sender_release_begin(&a)==-1);assert(wr_iot_mcu_sender_off_finish(s,7,0));
 assert(wr_iot_mcu_sender_release_begin(&a)==-1&&!s->release_claimed);
 assert(!held);return 0;}
