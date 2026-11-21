/* Prepared only. Claim/finish run under MacTabLock; the caller drops it around
 * native cache work while retaining this exact AUTH peer lease, then reacquires
 * it for owner revalidation and completion. Adapter/BSS lifetime is external.
 * auth_request is the current invocation handle published by AUTH. This borrows
 * the existing AUTH owner and never increments event_users. */
#ifndef WR_FT_IAPP_PEER_ADMISSION_H
#define WR_FT_IAPP_PEER_ADMISSION_H
#include "ft-peer-generation.h"
#include "ft-iapp-response-token.h"
static inline int wr_ft_iapp_peer_owned_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_peer_stamp *stamp)
{
 unsigned int i;
 if(!ad||!wr_ft_peer_current_locked(ad,stamp)||
    ad->wr_iot_peer_delete_active||ad->wr_iot_peer_table_owner.poisoned||
    !ad->wr_iot_peer_table_owner.transactions||
    ad->wr_assoc_event_users[stamp->wcid]!=1||
    ad->wr_assoc_generations[stamp->wcid]!=stamp->generation||
    ad->wr_assoc_visible[stamp->wcid]!=stamp->generation)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(ad->wr_assoc_addr[stamp->wcid][i]!=stamp->addr[i])return 0;
 return 1;
}

static inline int wr_ft_iapp_peer_request_begin_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_token_ledger *ledger, const unsigned char *token,
 const struct wr_ft_peer_stamp *stamp,
 struct wr_ft_iapp_token_handle *request)
{
 if(!request||request->serial||!wr_ft_iapp_peer_owned_locked(ad,stamp))return 0;
 return wr_ft_iapp_token_reserve_locked(ledger,token,stamp->bss,stamp->wcid,
  stamp->generation,stamp->addr,ad->ApCfg.MBSSID[stamp->bss].wdev.bssid,request);
}

static inline int wr_ft_iapp_peer_admit_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_token_ledger *ledger, const unsigned char *token,
 const unsigned char *mac, const unsigned char *r1khid,
 const struct wr_ft_peer_stamp *stamp,
 const struct wr_ft_iapp_token_handle *auth_request,
 struct wr_ft_iapp_token_handle *response)
{
 const struct wr_ft_iapp_token_entry *request;
 if(response && response==auth_request)return 0;
 wr_ft_iapp_token_clear(response);
 if(!ledger||!auth_request||!auth_request->serial||
    auth_request->slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 request=&ledger->entry[auth_request->slot];
 if(request->state!=WR_FT_IAPP_TOKEN_WAITING||request->invalidated||
    request->serial!=auth_request->serial||
    !wr_ft_iapp_token_equal(request->token,token))return 0;
 if(!response||!wr_ft_iapp_peer_owned_locked(ad,stamp))return 0;
 return wr_ft_iapp_token_claim_context_locked(ledger,token,mac,r1khid,
  stamp->bss,stamp->wcid,stamp->generation,stamp->addr,
  ad->ApCfg.MBSSID[stamp->bss].wdev.bssid,response);
}

/* AUTH exit must use this paired boundary while holding MacTabLock.
 * Failure preserves the peer scope for the outstanding claimed response. */
static inline int wr_ft_iapp_peer_request_end_locked(RTMP_ADAPTER *ad,
 struct wr_ft_peer_scope *scope, struct wr_ft_iapp_token_ledger *ledger,
 struct wr_ft_iapp_token_handle *request)
{
 unsigned int i;
 const struct wr_ft_iapp_token_entry *entry;
 if(!ad||!scope||!scope->active||scope->adapter!=ad||!ledger||!request||
    !wr_ft_peer_current_locked(ad,&scope->stamp))return 0;
 if(request->serial){
  if(request->slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
  entry=&ledger->entry[request->slot];
  if(entry->serial==request->serial){
   if(entry->bss!=scope->stamp.bss||entry->wcid!=scope->stamp.wcid||
      entry->generation!=scope->stamp.generation)return 0;
   for(i=0;i<MAC_ADDR_LEN;i++)
    if(entry->mac[i]!=scope->stamp.addr[i])return 0;
  }
 }
 if(!wr_ft_iapp_token_request_end_locked(ledger,request))return 0;
 return 1;
}


static inline int wr_ft_iapp_peer_leave_locked(RTMP_ADAPTER *ad,
 struct wr_ft_peer_scope *scope, struct wr_ft_iapp_token_ledger *ledger,
 struct wr_ft_iapp_token_handle *request)
{
 if(!wr_ft_iapp_peer_request_end_locked(ad,scope,ledger,request))return 0;
 return wr_ft_peer_leave_locked(ad,scope);
}

static inline int wr_ft_iapp_peer_advance_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry, struct wr_ft_peer_scope *scope,
 struct wr_ft_iapp_token_ledger *ledger,
 struct wr_ft_iapp_token_handle *request)
{
 if(!ad||!scope||!scope->active||scope->adapter!=ad||
    !wr_ft_iapp_peer_owned_locked(ad,&scope->stamp)||
    entry!=&ad->MacTab.Content[scope->stamp.wcid])return 0;
 if(!wr_ft_iapp_peer_request_end_locked(ad,scope,ledger,request))return 0;
 return wr_ft_peer_advance_locked(ad,entry,scope);
}

#endif
