#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>
typedef void VOID;typedef unsigned long ULONG;
typedef struct adapter {int wr_iot_transition_lock;int wr_iot_ticket_wait;struct wr_iot_radio_transition wr_iot_transition;} RTMP_ADAPTER;
static int held,pse,pdma,again,rtnl_held,wakes;
#define WR_IOT_RESET_TEST
static int rtnl_trylock(void){assert(!held);if(rtnl_held)return 0;rtnl_held=1;return 1;}
static void rtnl_unlock(void){assert(rtnl_held&&!held);rtnl_held=0;}
VOID PDMAResetAndRecovery(RTMP_ADAPTER *ad);
#define RTMP_IRQ_LOCK(lock,flags) ((void)(lock),(flags)=0,assert(!held),held=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define wake_up_all(wait) do { (void)(wait); assert(!held&&!rtnl_held); wakes++; } while(0)
static void wr_iot_pdma_reset_raw(RTMP_ADAPTER *ad){assert(!held&&rtnl_held&&ad->wr_iot_transition.busy==WR_RADIO_RESET);pdma++;}
static void wr_iot_pse_reset_raw(RTMP_ADAPTER *ad){
 assert(!held&&rtnl_held&&ad->wr_iot_transition.busy==WR_RADIO_RESET);pse++;
 wr_iot_pdma_reset_raw(ad);
 if(again)PDMAResetAndRecovery(ad);
}
#include "reset-admission.inc"
int main(void){
 RTMP_ADAPTER a={0};struct wr_iot_radio_ticket t;
 wr_iot_radio_transition_init(&a.wr_iot_transition);
 assert(wr_iot_radio_begin(&a.wr_iot_transition,a.wr_iot_transition.epoch,WR_RADIO_START,&t));
 PSEResetAndRecovery(&a);assert(!pse&&!pdma&&a.wr_iot_transition.reset_pending&&!wakes);
 assert(wr_iot_radio_finish_unverified(&a.wr_iot_transition,&t));
 again=1;wr_iot_radio_reset_drain(&a);
 assert(pse==1&&pdma==1&&!held&&!a.wr_iot_transition.busy&&!a.wr_iot_transition.main_ready&&wakes==1);
 assert(a.wr_iot_transition.reset_pending==WR_RADIO_RESET_PDMA);
 again=0;wr_iot_radio_reset_drain(&a);
 assert(pse==1&&pdma==2&&!a.wr_iot_transition.reset_pending&&wakes==2);
 PDMAResetAndRecovery(&a);assert(pdma==3&&!held&&wakes==3);
 /* Simulate stop/ioctl holding RTNL: no blocking or hardware mutation,
  * retained request executes only after the external owner releases it. */
 rtnl_held=1;PDMAResetAndRecovery(&a);
 assert(pdma==3&&a.wr_iot_transition.reset_pending&&!held&&rtnl_held&&wakes==3);
 rtnl_held=0;wr_iot_radio_reset_drain(&a);
 assert(pdma==4&&!a.wr_iot_transition.reset_pending&&!rtnl_held&&wakes==4);
 wr_iot_radio_request_close(&a.wr_iot_transition);
 PSEResetAndRecovery(&a);assert(pse==1&&pdma==4&&!held&&!rtnl_held&&wakes==4);
 puts("PASS real reset wrapper fragment: busy deferral, nested raw PSE/PDMA, retained second request, explicit retry and no readiness claim; hardware mocked");return 0;
}
