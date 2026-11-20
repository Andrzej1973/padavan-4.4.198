/* Prepared only. Caller holds MacTabLock from admission through cache update,
 * counter/completion changes and token finish; adapter/BSS lifetime is external.
 * auth_request must be the current invocation handle published by AUTH.
 * This borrows the existing AUTH owner and never increments event_users. */
#ifndef WR_FT_IAPP_PEER_ADMISSION_H
#define WR_FT_IAPP_PEER_ADMISSION_H
#include "ft-peer-generation.h"
#include "ft-iapp-response-token.h"
static inline int wr_ft_iapp_peer_admit_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_token_ledger *ledger, const unsigned char *token,
 const unsigned char *mac, const unsigned char *r1khid,
 const struct wr_ft_peer_stamp *stamp,
 const struct wr_ft_iapp_token_handle *auth_request,
 struct wr_ft_iapp_token_handle *response)
{
 unsigned int i;
 const struct wr_ft_iapp_token_entry *request;
 wr_ft_iapp_token_clear(response);
 if(!ledger||!auth_request||!auth_request->serial||
    auth_request->slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 request=&ledger->entry[auth_request->slot];
 if(request->state!=WR_FT_IAPP_TOKEN_WAITING||request->invalidated||
    request->serial!=auth_request->serial||
    !wr_ft_iapp_token_equal(request->token,token))return 0;
 if(!response||!ad||!wr_ft_peer_current_locked(ad,stamp)||
    ad->wr_iot_peer_delete_active||ad->wr_iot_peer_table_owner.poisoned||
    !ad->wr_iot_peer_table_owner.transactions||
    ad->wr_assoc_event_users[stamp->wcid]!=1||
    ad->wr_assoc_generations[stamp->wcid]!=stamp->generation||
    ad->wr_assoc_visible[stamp->wcid]!=stamp->generation)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(ad->wr_assoc_addr[stamp->wcid][i]!=stamp->addr[i])return 0;
 return wr_ft_iapp_token_claim_context_locked(ledger,token,mac,r1khid,
  stamp->bss,stamp->wcid,stamp->generation,stamp->addr,
  ad->ApCfg.MBSSID[stamp->bss].wdev.bssid,response);
}
#endif
