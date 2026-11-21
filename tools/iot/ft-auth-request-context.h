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
/* AUTH exit retires a completed response handle or detaches an unanswered
 * request. CLAIMED remains exclusively owned by response transfer. */
static inline int wr_ft_auth_request_exit_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state)
{
 unsigned int w,i;struct wr_ft_iapp_token_handle request;
 struct wr_ft_iapp_token_entry *item;
 unsigned int existing,pending;
 if(!ad||!state||!context)return 0;
 existing=context->existing&&context->existing->active;
 pending=context->pending&&context->pending->active;
 if(existing==pending)return 0;
 w=existing?context->existing->stamp.wcid:context->pending->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||w>=MAX_LEN_OF_MAC_TABLE)return 0;
 /* Successful AUTH can retire its request before exit cleanup runs. In that
  * case there is no request-owned state to inspect, and the pinned peer scope
  * remains responsible for its own release. Do not dereference entry until a
  * live request requires full invocation validation. */
 if(!state->current[w].serial)return 1;
 if(!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 request=state->current[w];
 if(request.slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 item=&state->ledger.entry[request.slot];
 if(item->serial!=request.serial||item->wcid!=w||
    item->bss!=entry->func_tb_idx||item->generation!=entry->assoc_gen)return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(item->mac[i]!=entry->Addr[i]||item->bssid[i]!=entry->wdev->bssid[i])return 0;
 if(item->state==WR_FT_IAPP_TOKEN_CLAIMED)return 0;
 if(item->state==WR_FT_IAPP_TOKEN_WAITING)
  return wr_ft_auth_request_detach_locked(ad,entry,context,state,&request);
 if(item->state==WR_FT_IAPP_TOKEN_FREE&&item->invalidated){
  wr_ft_iapp_token_clear(&state->current[w]);
  return 1;
 }
 return 0;
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
/* Before publishing SST_AUTH/generation, retire a detached predecessor and
 * clear first-peer provenance under the same table lock and live AUTH lease.
 * A synchronous outstanding request must use its own unpublish boundary. */
static inline int wr_ft_auth_request_success_prepare_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state)
{
 unsigned int w,i;struct wr_ft_iapp_token_handle previous,current;
 const struct wr_ft_preauth_identity *identity;
 if(!state||!wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
 if(state->current[w].serial){
  const struct wr_ft_iapp_token_entry *item;
  current=state->current[w];
  if(current.slot>=WR_FT_IAPP_TOKEN_CAPACITY)return 0;
  item=&state->ledger.entry[current.slot];
  if(item->serial!=current.serial||
     (item->invalidated&&item->state!=WR_FT_IAPP_TOKEN_FREE)||
     item->wcid!=w||item->bss!=entry->func_tb_idx||
     item->generation!=entry->assoc_gen)return 0;
  for(i=0;i<MAC_ADDR_LEN;i++)
   if(item->mac[i]!=entry->Addr[i]||item->bssid[i]!=entry->wdev->bssid[i])return 0;
  if(item->state==WR_FT_IAPP_TOKEN_CLAIMED)return 0;
  if(item->state==WR_FT_IAPP_TOKEN_WAITING &&
     (!state->detached[w]||
      !wr_ft_iapp_token_cancel_waiting_locked(&state->ledger,&current)))return 0;
  else if(item->state!=WR_FT_IAPP_TOKEN_FREE &&
          item->state!=WR_FT_IAPP_TOKEN_WAITING)return 0;
  if(item->state==WR_FT_IAPP_TOKEN_FREE&&item->invalidated&&state->detached[w])
   state->detached[w]=state->detached_sst[w]=0;
  wr_ft_iapp_token_clear(&state->current[w]);
 }
 identity=&state->preauth[w];
 if(identity->serial){
  if(identity->wcid!=w||identity->bss!=entry->func_tb_idx||
     identity->generation!=entry->assoc_gen)return 0;
  for(i=0;i<6;i++)
   if(identity->mac[i]!=entry->Addr[i]||identity->bssid[i]!=entry->wdev->bssid[i])return 0;
 }
 if(state->current[w].serial){
  previous=state->current[w];
  if(!wr_ft_auth_request_retire_detached_locked(ad,entry,context,state,&previous))return 0;
 }else if(state->detached[w])return 0;
 state->preauth[w]=(struct wr_ft_preauth_identity){0};
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
/* Reuse the same request token for native hard retries. A concurrent response
 * claim is reported separately so the caller waits without re-enqueueing it. */
static inline int wr_ft_auth_request_wire_token_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry,const struct wr_ft_auth_request_context *context,
 struct wr_ft_iapp_request_state *state,
 struct wr_ft_iapp_token_handle *request,unsigned char *token,
 unsigned int *response_claimed)
{
 unsigned int i,w;struct wr_ft_iapp_token_entry *item;
 if(response_claimed)*response_claimed=0;
 if(!token||(state&&token==state->token_counter))return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=0;
 if(!ad||!entry||!context||!state||!request||
    !wr_ft_auth_request_current_locked(ad,entry,context))return 0;
 if(!request->serial)
  return wr_ft_auth_request_publish_next_locked(ad,entry,context,state,
   request,token);
 w=entry->wcid;
 if(w>=WR_FT_IAPP_TOKEN_CAPACITY||request->slot>=WR_FT_IAPP_TOKEN_CAPACITY||
    state->current[w].serial!=request->serial||
    state->current[w].slot!=request->slot)return 0;
 item=&state->ledger.entry[request->slot];
 if(item->serial!=request->serial||item->bss!=entry->func_tb_idx||
    item->wcid!=w||item->generation!=entry->assoc_gen||item->invalidated||
    !wr_ft_iapp_token_nonzero(item->token))
  return 0;
 for(i=0;i<MAC_ADDR_LEN;i++)
  if(item->mac[i]!=entry->Addr[i]||item->bssid[i]!=entry->wdev->bssid[i])return 0;
 if(item->state==WR_FT_IAPP_TOKEN_CLAIMED){
  if(response_claimed)*response_claimed=1;
  return 1;
 }
 if(item->state!=WR_FT_IAPP_TOKEN_WAITING)return 0;
 for(i=0;i<WR_FT_IAPP_TOKEN_BYTES;i++)token[i]=item->token[i];
 return 1;
}
#endif
