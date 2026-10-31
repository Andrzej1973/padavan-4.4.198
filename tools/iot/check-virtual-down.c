#include "radio-transition.h"
#include <assert.h>
#include <stddef.h>
typedef int INT;typedef unsigned long ULONG;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
typedef struct {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;unsigned int VirtualIfCnt;void *net_dev;} RTMP_ADAPTER;
static int held,result,calls;
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,assert(!held),held=1,(void)(lock))
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define VIRTUAL_IF_DEC(ad) ((ad)->VirtualIfCnt--)
static int wr_iot_rt28xx_close_checked(void *dev,const struct wr_iot_radio_ticket *t){assert(!held&&dev&&t);calls++;return result;}
#include "virtual-down-checked.inc"
int main(void){RTMP_ADAPTER a={0};struct wr_iot_radio_ticket t,bad;wr_iot_radio_transition_init(&a.wr_iot_transition);a.net_dev=&a;a.VirtualIfCnt=2;a.wr_iot_transition.phase=WR_RADIO_READY;
assert(wr_iot_radio_begin_stop(&a.wr_iot_transition,2,&t));assert(wr_iot_virtual_down_checked(&a,&t)==0&&a.VirtualIfCnt==1&&!calls);assert(wr_iot_virtual_down_checked(&a,&t)==0&&a.VirtualIfCnt==1&&!calls);assert(wr_iot_radio_finish(&a.wr_iot_transition,&t,1));
assert(wr_iot_radio_begin_stop(&a.wr_iot_transition,1,&t));result=-1;assert(wr_iot_virtual_down_checked(&a,&t)==1&&!a.VirtualIfCnt&&calls==1&&a.wr_iot_transition.virtual_down_stage==1);bad=t;bad.serial++;assert(wr_iot_virtual_down_checked(&a,&bad)==1&&calls==1);result=0;assert(wr_iot_virtual_down_checked(&a,&t)==0&&!a.VirtualIfCnt&&calls==2);assert(wr_iot_virtual_down_checked(&a,&t)==0&&calls==2&&!held);
wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_READY;a.wr_iot_transition.main_ready=1;a.VirtualIfCnt=3;calls=0;
assert(wr_iot_radio_begin_aux_stop(&a.wr_iot_transition,3,&t)&&t.operation==WR_RADIO_AUX_CLOSE);
assert(wr_iot_virtual_down_checked(&a,&t)==0&&a.VirtualIfCnt==2&&!calls);
assert(wr_iot_virtual_down_checked(&a,&t)==0&&a.VirtualIfCnt==2&&!calls);
assert(wr_iot_radio_finish(&a.wr_iot_transition,&t,1));return 0;}
