/* Host bridge test with injected physical close; not hardware verification. */
#include "radio-transition.h"
#include <assert.h>
#include <stddef.h>
typedef int INT;
typedef void VOID;
typedef unsigned long ULONG;
#define NDIS_STATUS_SUCCESS 0
#define WIFI_DIAG
struct adapter {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;};
typedef struct adapter *PRTMP_ADAPTER;
struct net_device {PRTMP_ADAPTER priv;};
static int held,result,closes,diagnostics;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->priv)
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,assert(!held),held=1,(void)(lock))
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
static int wr_iot_drv_close_checked(void *ad,void *dev,const struct wr_iot_radio_ticket *t){
 struct adapter *a=ad;
 assert(ad&&dev&&t&&!held);closes++;
 if(t->operation!=WR_RADIO_CLOSE||a->wr_iot_transition.busy!=WR_RADIO_CLOSE||
    t->serial!=a->wr_iot_transition.serial)return 1;
 return result;
}
static void DiagProcExit(void *ad){assert(ad&&!held);diagnostics++;}
#include "physical-close-result.inc"
int main(void){
 struct adapter a={0};struct net_device d={&a};struct wr_iot_radio_ticket t={0};
 wr_iot_radio_transition_init(&a.wr_iot_transition);
 wr_iot_radio_request_close(&a.wr_iot_transition);
 assert(wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,WR_RADIO_CLOSE,&t));
 assert(wr_iot_rt28xx_close_checked(NULL,&t)==-1);
 assert(wr_iot_rt28xx_close_checked(&d,NULL)==-1&&!closes);
 d.priv=NULL;assert(wr_iot_rt28xx_close_checked(&d,&t)==-1&&!closes);d.priv=&a;
 {struct wr_iot_radio_ticket stale=t;stale.serial++;
  assert(wr_iot_rt28xx_close_checked(&d,&stale)==-1&&closes==1&&!diagnostics);}
 result=1;assert(wr_iot_rt28xx_close_checked(&d,&t)==-1&&!diagnostics&&!a.wr_iot_transition.close_notified);
 result=0;assert(wr_iot_rt28xx_close_checked(&d,&t)==0&&diagnostics==1&&a.wr_iot_transition.close_notified);
 assert(wr_iot_rt28xx_close_checked(&d,&t)==0&&diagnostics==1&&!held&&closes==4);
 return 0;
}
