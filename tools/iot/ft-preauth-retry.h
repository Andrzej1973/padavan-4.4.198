/* Prepared only. This identifies a previously owned first-peer FT request,
 * never a generic inactive MAC-table entry. Caller holds MacTabLock and pins
 * adapter/BSS lifetime. Queue and callback must both revalidate this stamp. */
#ifndef WR_FT_PREAUTH_RETRY_H
#define WR_FT_PREAUTH_RETRY_H
#include "ft-iapp-detached-admission.h"
#include "ft-pending-peer-scope.h"
static inline int wr_ft_preauth_retry_capture_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_iapp_request_state *state,unsigned int w,unsigned int b,
 const unsigned char *mac,struct wr_ft_preauth_identity *out)
{
 const struct wr_ft_preauth_identity *identity;
 struct wr_ft_iapp_token_entry expected={0};unsigned int i;
 if(!out)return 0;
 if(state){
  for(i=0;i<WR_FT_IAPP_TOKEN_CAPACITY;i++)if(out==&state->preauth[i])return 0;
 }
 *out=(struct wr_ft_preauth_identity){0};
 if(!ad||!state||!mac||w==RESERVED_WCID||w>=WR_FT_IAPP_TOKEN_CAPACITY||
    w>=MAX_LEN_OF_MAC_TABLE||state->ledger.poisoned||
    ad->wr_iot_peer_delete_active||ad->wr_assoc_event_users[w]||
    !wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,0)||
    !wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor))return 0;
 identity=&state->preauth[w];
 if(!identity->serial||identity->wcid!=w||identity->bss!=b||
    __builtin_memcmp(identity->mac,mac,6))return 0;
 expected.wcid=w;expected.bss=b;expected.generation=identity->generation;
 for(i=0;i<6;i++){expected.mac[i]=identity->mac[i];expected.bssid[i]=identity->bssid[i];}
 if(!wr_ft_iapp_detached_identity_locked(ad,&expected,SST_NOT_AUTH))return 0;
 *out=*identity;return 1;
}
/* Callback consumes the original captured identity. This is not a new capture
 * of whichever generation currently occupies the queued WCID. */
static inline int wr_ft_preauth_retry_enter_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_iapp_request_state *state,
 const struct wr_ft_preauth_identity *expected,
 struct wr_ft_pending_peer_scope *scope,MAC_TABLE_ENTRY **out)
{
 struct wr_ft_preauth_identity current={0};unsigned int i,w;
 if(out)*out=NULL;
 if(!expected||!scope||scope->active||!out)return 0;
 if(!wr_ft_preauth_retry_capture_locked(ad,state,expected->wcid,
     expected->bss,expected->mac,&current))return 0;
 if(current.serial!=expected->serial||current.generation!=expected->generation||
    current.wcid!=expected->wcid||current.bss!=expected->bss)return 0;
 for(i=0;i<6;i++)
  if(current.mac[i]!=expected->mac[i]||current.bssid[i]!=expected->bssid[i])return 0;
 if(!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))return 0;
 w=expected->wcid;ad->wr_assoc_event_users[w]=1;
 scope->adapter=ad;scope->wcid=w;scope->bss=expected->bss;
 scope->generation=expected->generation;scope->active=1;
 for(i=0;i<6;i++)scope->addr[i]=expected->mac[i];
 *out=&ad->MacTab.Content[w];return 1;
}
#endif
