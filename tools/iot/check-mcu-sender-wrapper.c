#include "mcu-sender-owner.h"
#include <assert.h>
#include <stdlib.h>
typedef int INT32;typedef unsigned long ULONG;
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
#define EXT_CID 1
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
typedef struct {int wr_iot_mcu_sender_lock,wr_iot_mcu_sender_wait;struct wr_iot_mcu_sender_owner wr_iot_mcu_sender_owner;} ADAPTER,*PRTMP_ADAPTER;
struct cmd_msg {int cmd_type,ext_cmd_type,wr_iot_checked;};
static int held,calls,frees,wakes,code,close_inside,retired,nested_radio;
static ADAPTER *retire_target;
static void after_unlock(void){
 if(retire_target && retire_target->wr_iot_mcu_sender_owner.closed &&
    !retire_target->wr_iot_mcu_sender_owner.inflight){
  free(retire_target);retire_target=0;retired++;
 }
}
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;after_unlock();}while(0)
static void AndesForceFreeCmdMsg(struct cmd_msg *m){assert(m&&!held);frees++;}
static void wake_up_all(int *w){(void)w;assert(held);wakes++;}
INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad,struct cmd_msg *msg);
static int wr_iot_mcu_send_body(PRTMP_ADAPTER a,struct cmd_msg *m){
 assert(a&&m&&!held&&a->wr_iot_mcu_sender_owner.inflight==1);calls++;
 if(m->cmd_type==EXT_CID&&m->ext_cmd_type==EXT_CMD_RADIO_ON_OFF_CTRL)assert(m->wr_iot_checked==1);
 else assert(!m->wr_iot_checked);
 if(nested_radio){
  struct cmd_msg other={.cmd_type=EXT_CID,.ext_cmd_type=EXT_CMD_RADIO_ON_OFF_CTRL};int old_calls=calls;
  assert(a->wr_iot_mcu_sender_owner.radio_active);
  assert(AndesSendCmdMsg(a,&other)==-1&&calls==old_calls);
 }
 if(close_inside){assert(wr_iot_mcu_sender_close(&a->wr_iot_mcu_sender_owner,3));assert(!wr_iot_mcu_sender_off_begin(&a->wr_iot_mcu_sender_owner,3));}
 return code;
}
#include "mcu-sender-wrapper.inc"
int main(void){ADAPTER a={0};struct cmd_msg m={0};
 for(code=-4;code<=1;code++){
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);
 assert(AndesSendCmdMsg(&a,&m)==code);assert(!a.wr_iot_mcu_sender_owner.inflight&&!held);
 }
 assert(calls==6&&wakes==6&&!frees);
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);close_inside=1;code=0;
 assert(AndesSendCmdMsg(&a,&m)==0);assert(wr_iot_mcu_sender_off_begin(&a.wr_iot_mcu_sender_owner,3));
 assert(AndesSendCmdMsg(&a,&m)==-1&&calls==7&&frees==1);
 assert(AndesSendCmdMsg(0,&m)==-1);assert(AndesSendCmdMsg(&a,0)==-1);
 ADAPTER *heap=calloc(1,sizeof(*heap));assert(heap);
 wr_iot_mcu_sender_init(&heap->wr_iot_mcu_sender_owner);retire_target=heap;
 assert(AndesSendCmdMsg(heap,&m)==0);assert(retired==1&&!retire_target&&!held);
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);close_inside=0;code=-1;
 m.cmd_type=EXT_CID;m.ext_cmd_type=EXT_CMD_RADIO_ON_OFF_CTRL;
 assert(AndesSendCmdMsg(&a,&m)==-1);
 assert(a.wr_iot_mcu_sender_owner.uncertain&&a.wr_iot_mcu_sender_owner.closed);
 int previous=calls;assert(AndesSendCmdMsg(&a,&m)==-1&&calls==previous);
 assert(!wr_iot_mcu_sender_release_claim(&a.wr_iot_mcu_sender_owner));
 wr_iot_mcu_sender_init(&a.wr_iot_mcu_sender_owner);nested_radio=1;code=0;
 assert(AndesSendCmdMsg(&a,&m)==0&&!a.wr_iot_mcu_sender_owner.radio_active);
 nested_radio=0;assert(AndesSendCmdMsg(&a,&m)==0);
 return 0;}
