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
#endif
