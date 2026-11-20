/* Prepared only. MacTabLock is held continuously from enter through native
 * cache/counter work and finish. Adapter/BSS lifetime is external. Detached
 * replies own a new lease and must NEVER complete an AUTH wait. */
#ifndef WR_FT_IAPP_DETACHED_ADMISSION_H
#define WR_FT_IAPP_DETACHED_ADMISSION_H
#include "ft-peer-generation.h"
#include "ft-iapp-request-state.h"
#include "peer-close-executor.h"
struct wr_ft_iapp_detached_scope {
 RTMP_ADAPTER *adapter;
 struct wr_ft_iapp_request_state *state;
 struct wr_ft_peer_stamp stamp;
 struct wr_ft_iapp_token_handle response;
 unsigned int sst,active;
};
static inline int wr_ft_iapp_detached_identity_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_iapp_token_entry *request,unsigned int sst)
{
 unsigned int w,b,i;MAC_TABLE_ENTRY *entry;
 if(!ad||!request||!request->generation)return 0;
 w=request->wcid;b=request->bss;
 if(w==RESERVED_WCID||w>=MAX_LEN_OF_MAC_TABLE||b>=ad->ApCfg.BssidNum||
    b>=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))return 0;
 entry=&ad->MacTab.Content[w];
 if(!IS_ENTRY_CLIENT(entry)||entry->wcid!=w||entry->func_tb_idx!=b||
    entry->wdev!=&ad->ApCfg.MBSSID[b].wdev||(unsigned int)entry->Sst!=sst||
    (sst!=SST_NOT_AUTH&&sst!=SST_AUTH&&sst!=SST_ASSOC)||
    entry->assoc_gen!=request->generation||
    ad->wr_assoc_generations[w]!=request->generation||
    ad->wr_assoc_visible[w]!=request->generation)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(entry->Addr[i]!=request->mac[i]||ad->wr_assoc_addr[w][i]!=request->mac[i]||
     entry->wdev->bssid[i]!=request->bssid[i])return 0;
 return 1;
}
static inline int wr_ft_iapp_detached_enter_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_request_state *state,const unsigned char *token,
 const unsigned char *mac,const unsigned char *bssid,
 struct wr_ft_iapp_detached_scope *scope,MAC_TABLE_ENTRY **out)
{
 unsigned int i,j,w;struct wr_ft_iapp_token_entry *request;
 struct wr_ft_iapp_token_handle response={0};
 if(out)*out=NULL;
 if(!ad||!state||!scope||scope->active||!out||!mac||!bssid||
    state->ledger.poisoned||!wr_ft_iapp_token_nonzero(token)||
    ad->wr_iot_peer_delete_active||
    !wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor))return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++){
  request=&state->ledger.entry[i];
  if(request->state!=WR_FT_IAPP_TOKEN_WAITING||!request->serial||request->invalidated||
     !wr_ft_iapp_token_equal(request->token,token)||
     __builtin_memcmp(request->mac,mac,6)||__builtin_memcmp(request->bssid,bssid,6))continue;
  w=request->wcid;
  if(w>=WR_FT_IAPP_TOKEN_CAPACITY||!state->detached[w]||
     state->current[w].serial!=request->serial||state->current[w].slot!=i||
     !wr_ft_iapp_detached_identity_locked(ad,request,state->detached_sst[w])||
     ad->wr_assoc_event_users[w])return 0;
  if(!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))return 0;
  if(!wr_ft_iapp_token_claim_context_locked(&state->ledger,token,mac,bssid,
      request->bss,w,request->generation,request->mac,request->bssid,&response)){
   (void)wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner);return 0;
  }
  ad->wr_assoc_event_users[w]=1;
  scope->adapter=ad;scope->state=state;scope->response=response;
  scope->stamp.wcid=w;scope->stamp.bss=request->bss;
  scope->stamp.generation=request->generation;
  for(j=0;j<MAC_ADDR_LEN;j++)scope->stamp.addr[j]=request->mac[j];
  scope->sst=state->detached_sst[w];scope->active=1;
  *out=&ad->MacTab.Content[w];return 1;
 }
 return 0;
}
/* Cache failure also consumes this response. No ACK/completion is emitted by
 * this boundary. Uncertain identity retains the lease and poisons reset. */
static inline int wr_ft_iapp_detached_finish_locked(RTMP_ADAPTER *ad,
 struct wr_ft_iapp_request_state *state,struct wr_ft_iapp_detached_scope *scope)
{
 unsigned int w,i;const struct wr_ft_iapp_token_entry *request;
 if(!ad||!state||!scope||!scope->active||scope->adapter!=ad||scope->state!=state)return 0;
 w=scope->stamp.wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||scope->response.slot>=WR_FT_IAPP_TOKEN_CAPACITY||
    ad->wr_iot_peer_table_owner.poisoned||!ad->wr_iot_peer_table_owner.transactions||
    ad->wr_iot_peer_delete_active||
    !wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)||
    ad->wr_assoc_event_users[w]!=1||
    !state->detached[w]||state->detached_sst[w]!=scope->sst||
    state->current[w].slot!=scope->response.slot||
    state->current[w].serial!=scope->response.serial)goto uncertain;
 request=&state->ledger.entry[scope->response.slot];
 if(request->state!=WR_FT_IAPP_TOKEN_CLAIMED||request->invalidated||
    request->serial!=scope->response.serial||request->wcid!=w||
    request->bss!=scope->stamp.bss||request->generation!=scope->stamp.generation||
    !wr_ft_iapp_detached_identity_locked(ad,request,scope->sst))goto uncertain;
 for(i=0;i<MAC_ADDR_LEN;i++)if(request->mac[i]!=scope->stamp.addr[i])goto uncertain;
 if(!wr_ft_iapp_token_finish_locked(&state->ledger,&scope->response))goto uncertain;
 wr_ft_iapp_token_clear(&state->current[w]);
 state->detached[w]=state->detached_sst[w]=0;
 ad->wr_assoc_event_users[w]=0;
 scope->active=0;scope->adapter=NULL;scope->state=NULL;
 wr_ft_iapp_token_clear(&scope->response);
 return wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner);
uncertain:
 ad->wr_iot_peer_table_owner.poisoned=1;return 0;
}
#endif
