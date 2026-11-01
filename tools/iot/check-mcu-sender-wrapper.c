#include "mcu-sender-owner.h"
#include <assert.h>
typedef int INT32;typedef unsigned long ULONG;
#define NDIS_STATUS_FAILURE -1
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} ADAPTER,*PRTMP_ADAPTER;
struct cmd_msg {int unused;};
static int held,calls,frees,wakes,code,close_inside;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static void AndesForceFreeCmdMsg(struct cmd_msg *m){assert(m&&!held);frees++;}
static void wake_up_all(int *w){(void)w;assert(!held);wakes++;}
static int wr_iot_mcu_send_body(PRTMP_ADAPTER a,struct cmd_msg *m){
 assert(a&&m&&!held&&a->wr_iot_mcu_sender_owner.inflight==1);calls++;
 if(close_inside){assert(wr_iot_mcu_sender_close(&a->wr_iot_mcu_sender_owner,3));assert(!wr_iot_mcu_sender_off_begin(&a->wr_iot_mcu_sender_owner,3));}
 return code;
}
#include "mcu-sender-wrapper.inc"
int main(void){ADAPTER a={0};struct cmd_msg m;
 for(code=-4;code<=1;code++){
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);
 assert(AndesSendCmdMsg(&a,&m)==code);assert(!a.wr_iot_mcu_sender_owner.inflight&&!held);
 }
 assert(calls==6&&wakes==6&&!frees);
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);close_inside=1;code=0;
 assert(AndesSendCmdMsg(&a,&m)==0);assert(wr_iot_mcu_sender_off_begin(&a.wr_iot_mcu_sender_owner,3));
 assert(AndesSendCmdMsg(&a,&m)==-1&&calls==7&&frees==1);
 assert(AndesSendCmdMsg(0,&m)==-1);assert(AndesSendCmdMsg(&a,0)==-1);
 return 0;}
