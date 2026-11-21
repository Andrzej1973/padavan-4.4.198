/* Prepared retry callback boundary. Caller holds MacTabLock and owns the
 * dequeued MLME element, adapter and BSS lifetime. No current stamp recapture. */
#ifndef WR_FT_AUTH_RETRY_PEER_SCOPE_H
#define WR_FT_AUTH_RETRY_PEER_SCOPE_H
#include "ft-auth-peer-scope.h"
#include "ft-preauth-queue.h"
#include "ft-preauth-retry.h"
static inline int wr_ft_auth_retry_enter_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_iapp_request_state *state,const MLME_QUEUE_ELEM *event,
 unsigned int bss,const unsigned char *mac,
 struct wr_ft_pending_peer_scope *scope,MAC_TABLE_ENTRY **entry)
{
 struct wr_ft_preauth_identity expected={0};unsigned int i;
 if(!entry)return 0;
 *entry=NULL;
 if(!event||!scope||scope->active||event->ft_pending_generation||
    !wr_ft_auth_event_matches(ad,event,bss,mac)||
    !wr_ft_preauth_elem_snapshot(event,&expected)||expected.bss!=bss||
    event->assoc_gen!=expected.generation||event->assoc_wcid!=expected.wcid||
    event->Wcid!=expected.wcid)return 0;
 for(i=0;i<6;i++)
  if(expected.mac[i]!=mac[i]||event->assoc_addr[i]!=mac[i]||
     expected.bssid[i]!=ad->ApCfg.MBSSID[bss].wdev.bssid[i])return 0;
 return wr_ft_preauth_retry_enter_locked(ad,state,&expected,scope,entry);
}
#endif
