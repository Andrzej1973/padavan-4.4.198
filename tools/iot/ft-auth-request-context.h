/* Prepared only. Stack-owned invocation context, never retained by IAPP.
 * Caller keeps exactly one peer scope alive through the synchronous AUTH call.
 * All validation requires MacTabLock and external adapter/BSS lifetime. */
#ifndef WR_FT_AUTH_REQUEST_CONTEXT_H
#define WR_FT_AUTH_REQUEST_CONTEXT_H
#include "ft-iapp-peer-admission.h"
#include "ft-iapp-pending-admission.h"
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
#endif
