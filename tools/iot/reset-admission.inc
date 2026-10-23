/* Candidate wrapper; caller pins adapter lifetime. No waits under short lock.
 * Raw PSE calls raw PDMA, never the public wrapper recursively. */
#ifndef WR_IOT_RESET_TEST
#include <linux/rtnetlink.h>
#endif
VOID wr_iot_radio_reset_drain(RTMP_ADAPTER *pAd)
{
 struct wr_iot_radio_ticket ticket;
 ULONG flags;
 int admitted=0;
 /* ndo_open/ndo_stop already hold RTNL. Never wait here: stop may join
  * this command worker, or an ioctl caller may itself already own RTNL. */
 if(!rtnl_trylock())return;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 if(pAd->wr_iot_transition.reset_pending)
  admitted=wr_iot_radio_begin(&pAd->wr_iot_transition,
    pAd->wr_iot_transition.epoch,WR_RADIO_RESET,&ticket);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 if(!admitted){rtnl_unlock();return;}
 if(ticket.reset_kind&WR_RADIO_RESET_PSE)wr_iot_pse_reset_raw(pAd);
 else wr_iot_pdma_reset_raw(pAd);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 /* VOID raw return is not hardware success/readiness evidence. */
 wr_iot_radio_finish_unverified(&pAd->wr_iot_transition,&ticket);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 rtnl_unlock();
}
static VOID wr_iot_request_driver_reset(RTMP_ADAPTER *pAd,unsigned int kind)
{
 ULONG flags;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 wr_iot_radio_request_reset_kind(&pAd->wr_iot_transition,kind);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 wr_iot_radio_reset_drain(pAd);
}
VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd)
{ wr_iot_request_driver_reset(pAd,WR_RADIO_RESET_PDMA); }
VOID PSEResetAndRecovery(RTMP_ADAPTER *pAd)
{ wr_iot_request_driver_reset(pAd,WR_RADIO_RESET_PSE); }
