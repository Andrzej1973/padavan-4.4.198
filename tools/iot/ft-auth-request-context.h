/* Prepared only. Stack-owned invocation context, never retained by IAPP.
 * Caller keeps exactly one peer scope alive through the synchronous AUTH call.
 * All validation requires MacTabLock and external adapter/BSS lifetime. */
#ifndef WR_FT_AUTH_REQUEST_CONTEXT_H
#define WR_FT_AUTH_REQUEST_CONTEXT_H
#include "ft-iapp-peer-admission.h"
#include "ft-iapp-pending-admission.h"
#include "ft-iapp-request-state.h"
struct wr_ft_auth_request_context {
 struct wr_ft_peer_scope *existing;
 struct wr_ft_pending_peer_scope *pending;
};
static inline int wr_ft_auth_request_current_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context)
{
 unsigned int existing,pending;
 if(!ad||!entry||!context)return 0;
 existing=context->existing&&context->existing->active;
 pending=context->pending&&context->pending->active;
 if(existing==pending)return 0;
 if(existing){
  const struct wr_ft_peer_scope *scope=context->existing;
  return scope->adapter==ad&&wr_ft_iapp_peer_owned_locked(ad,&scope->stamp)&&
   entry==&ad->MacTab.Content[scope->stamp.wcid];
 }
 return wr_ft_iapp_pending_owned_locked(ad,context->pending)&&
  entry==&ad->MacTab.Content[context->pending->wcid];
}
/* Request handles are explicit invocation inputs, never inferred by MAC/WCID.
 * The caller owns ledger lifetime and holds MacTabLock through each operation. */
static inline int wr_ft_auth_request_begin_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_token_ledger *ledger,const unsigned char *token,
 struct wr_ft_iapp_token_handle *request)
{
 if(!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 if(context->existing&&context->existing->active)
  return wr_ft_iapp_peer_request_begin_locked(ad,ledger,token,
   &context->existing->stamp,request);
 return wr_ft_iapp_pending_request_begin_locked(ad,ledger,token,
  context->pending,request);
}
static inline int wr_ft_auth_request_admit_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_token_ledger *ledger,const unsigned char *token,
 const unsigned char *mac,const unsigned char *bssid,
 const struct wr_ft_iapp_token_handle *request,
 struct wr_ft_iapp_token_handle *response)
{
 if(response&&response==request)return 0;
 wr_ft_iapp_token_clear(response);
 if(!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 if(context->existing&&context->existing->active)
  return wr_ft_iapp_peer_admit_locked(ad,ledger,token,mac,bssid,
   &context->existing->stamp,request,response);
 return wr_ft_iapp_pending_admit_locked(ad,ledger,token,mac,bssid,
  context->pending,request,response);
}
static inline int wr_ft_auth_request_end_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_token_ledger *ledger,
 struct wr_ft_iapp_token_handle *request)
{
 if(!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 if(context->existing&&context->existing->active)
  return wr_ft_iapp_peer_request_end_locked(ad,context->existing,ledger,request);
 return wr_ft_iapp_pending_request_end_locked(ad,context->pending,ledger,request);
}
/* Publish only value handles. A stale invocation cannot end a later request,
 * even when the same WCID and ledger slot have both been reused. */
static inline int wr_ft_auth_request_publish_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,const unsigned char *token,
 struct wr_ft_iapp_token_handle *request)
{
 unsigned int w,i;
 if(!state||!request||request->serial||
    !wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||state->current[w].serial||state->detached[w])return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  if(request==&state->current[i])return 0;
 if(!wr_ft_auth_request_begin_locked(ad,entry,context,&state->ledger,token,request))return 0;
 state->current[w]=*request;
 return 1;
}
static inline int wr_ft_auth_request_unpublish_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,struct wr_ft_iapp_token_handle *request)
{
 unsigned int w,i;
 if(!state||!request||!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||state->detached[w])return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  if(request==&state->current[i])return 0;
 if(state->current[w].serial!=request->serial||
    (request->serial&&state->current[w].slot!=request->slot))return 0;
 if(!wr_ft_auth_request_end_locked(ad,entry,context,&state->ledger,request))return 0;
 wr_ft_iapp_token_clear(&state->current[w]);
 return 1;
}
/* Soft retry returns before IAPP delivery. Transfer only the published value
 * handle to the adapter; caller still leaves its peer scope separately. A
 * detached response must acquire its own exact-generation lease and must not
 * signal a later AUTH invocation's completion. */
static inline int wr_ft_auth_request_detach_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,struct wr_ft_iapp_token_handle *request)
{
 unsigned int w,i;const struct wr_ft_iapp_token_entry *pending;
 if(!state||!request||!request->serial||
    !wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||state->detached[w]||
    request->slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  if(request==&state->current[i])return 0;
 if(state->current[w].serial!=request->serial||
    state->current[w].slot!=request->slot)return 0;
 pending=&state->ledger.entry[request->slot];
 if(pending->state!=WR_FT_IAPP_TOKEN_WAITING||pending->invalidated||
    pending->serial!=request->serial||state->ledger.poisoned||
    pending->wcid!=w||pending->bss!=entry->func_tb_idx||
    pending->generation!=entry->assoc_gen)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(pending->mac[i]!=entry->Addr[i]||pending->bssid[i]!=entry->wdev->bssid[i])return 0;
 state->detached[w]=1;
 state->detached_sst[w]=entry->Sst;
 if(context->pending&&context->pending->active){
  struct wr_ft_preauth_identity *identity=&state->preauth[w];
  identity->serial=request->serial;identity->generation=entry->assoc_gen;
  identity->bss=entry->func_tb_idx;identity->wcid=w;
  for(i=0;i<MAC_ADDR_LEN;i++){
   identity->mac[i]=entry->Addr[i];identity->bssid[i]=entry->wdev->bssid[i];
  }
 }
 wr_ft_iapp_token_clear(request);
 return 1;
}
/* A new synchronous AUTH owner may cancel its exact detached predecessor
 * before retry publication. An old serial or a claimed response is immutable
 * here; delete/generation retirement requires its own owner boundary. */
static inline int wr_ft_auth_request_retire_detached_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,
 const struct wr_ft_iapp_token_handle *expected)
{
 unsigned int w,i;const struct wr_ft_iapp_token_entry *pending;
 if(!state||!expected||!expected->serial||
    !wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||!state->detached[w]||
    expected->slot>=WR_FT_IAPP_TOKEN_CAPACITY||
    state->current[w].serial!=expected->serial||
    state->current[w].slot!=expected->slot||
    state->detached_sst[w]!=(unsigned int)entry->Sst)return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)
  if(expected==&state->current[i])return 0;
 pending=&state->ledger.entry[expected->slot];
 if(pending->state!=WR_FT_IAPP_TOKEN_WAITING||pending->invalidated||
    pending->serial!=expected->serial||pending->wcid!=w||
    pending->bss!=entry->func_tb_idx||pending->generation!=entry->assoc_gen)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(pending->mac[i]!=entry->Addr[i]||pending->bssid[i]!=entry->wdev->bssid[i])return 0;
 if(!wr_ft_iapp_token_cancel_waiting_locked(&state->ledger,expected))return 0;
 wr_ft_iapp_token_clear(&state->current[w]);
 state->detached[w]=state->detached_sst[w]=0;
 return 1;
}
/* Return a wire token only after its request handle is published. Failed
 * publication consumes sequence space but never exposes an unowned token. */
static inline int wr_ft_auth_request_publish_next_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,
 struct wr_ft_iapp_token_handle *request,unsigned char *token)
{
 unsigned char next[WR_FT_IAPP_TOKEN_BYTES];unsigned int i;
 if(!token||(state&&token==state->token_counter))return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=0;
 if(!wr_ft_auth_request_current_locked(ad,entry,context)||
    !wr_ft_iapp_request_next_token_locked(state,next))return 0;
 if(!wr_ft_auth_request_publish_locked(ad,entry,context,state,next,request))return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=next[i];
 return 1;
}
#endif
