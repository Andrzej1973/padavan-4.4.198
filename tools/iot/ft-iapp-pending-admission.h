/* Prepared only. MacTabLock and adapter/BSS lifetime are caller preconditions.
 * A pre-auth entry is admissible solely through its private published scope. */
#ifndef WR_FT_IAPP_PENDING_ADMISSION_H
#define WR_FT_IAPP_PENDING_ADMISSION_H
#include "ft-pending-peer-scope.h"
#include "ft-iapp-response-token.h"
static inline int wr_ft_iapp_pending_owned_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_pending_peer_scope *scope)
{
 MAC_TABLE_ENTRY *entry;unsigned int i,w;
 if(!ad||!scope||!scope->active||scope->adapter!=ad||!scope->generation||
    scope->wcid==RESERVED_WCID||scope->wcid>=MAX_LEN_OF_MAC_TABLE||
    scope->bss>=ad->ApCfg.BssidNum||
    scope->bss>=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])||
    ad->wr_iot_peer_delete_active||ad->wr_iot_peer_table_owner.poisoned||
    !ad->wr_iot_peer_table_owner.transactions)return 0;
 w=scope->wcid;entry=&ad->MacTab.Content[w];
 if(!IS_ENTRY_CLIENT(entry)||entry->wcid!=w||entry->Sst!=SST_NOT_AUTH||
    entry->func_tb_idx!=scope->bss||
    entry->wdev!=&ad->ApCfg.MBSSID[scope->bss].wdev||
    entry->assoc_gen!=scope->generation||ad->wr_assoc_event_users[w]!=1||
    ad->wr_assoc_generations[w]!=scope->generation||
    ad->wr_assoc_visible[w]!=scope->generation)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(entry->Addr[i]!=scope->addr[i]||ad->wr_assoc_addr[w][i]!=scope->addr[i])return 0;
 return 1;
}

static inline int wr_ft_iapp_pending_request_begin_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_token_ledger *ledger,const unsigned char *token,
 const struct wr_ft_pending_peer_scope *scope,
 struct wr_ft_iapp_token_handle *request)
{
 if(!request||request->serial||!wr_ft_iapp_pending_owned_locked(ad,scope))return 0;
 return wr_ft_iapp_token_reserve_locked(ledger,token,scope->bss,scope->wcid,
  scope->generation,scope->addr,ad->ApCfg.MBSSID[scope->bss].wdev.bssid,request);
}
static inline int wr_ft_iapp_pending_admit_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_token_ledger *ledger,const unsigned char *token,
 const unsigned char *mac,const unsigned char *bssid,
 const struct wr_ft_pending_peer_scope *scope,
 const struct wr_ft_iapp_token_handle *request,
 struct wr_ft_iapp_token_handle *response)
{
 const struct wr_ft_iapp_token_entry *entry;
 if(response&&response==request)return 0;
 wr_ft_iapp_token_clear(response);
 if(!response||!ledger||!request||!request->serial||
    request->slot>=WR_FT_IAPP_TOKEN_CAPACITY||
    !wr_ft_iapp_pending_owned_locked(ad,scope))return 0;
 entry=&ledger->entry[request->slot];
 if(entry->serial!=request->serial||entry->state!=WR_FT_IAPP_TOKEN_WAITING||
    entry->invalidated||!wr_ft_iapp_token_equal(entry->token,token))return 0;
 return wr_ft_iapp_token_claim_context_locked(ledger,token,mac,bssid,
  scope->bss,scope->wcid,scope->generation,scope->addr,
  ad->ApCfg.MBSSID[scope->bss].wdev.bssid,response);
}
#endif
