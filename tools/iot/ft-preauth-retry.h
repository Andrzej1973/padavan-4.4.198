/* Prepared only. This identifies a previously owned first-peer FT request,
 * never a generic inactive MAC-table entry. Caller holds MacTabLock and pins
 * adapter/BSS lifetime. Queue and callback must both revalidate this stamp. */
#ifndef WR_FT_PREAUTH_RETRY_H
#define WR_FT_PREAUTH_RETRY_H
#include "ft-iapp-detached-admission.h"
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
#endif
