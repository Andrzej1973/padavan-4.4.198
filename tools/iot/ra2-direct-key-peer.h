/* Caller owns MacTabLock, the exclusive ra2 key arbiter, and a successful
 * wr_ra2_rekey_peer_scope until native key execution finishes. This lookup
 * neither takes a lock nor manufactures a station/firmware lifetime token. */
#ifndef WR_IOT_RA2_DIRECT_KEY_PEER_H
#define WR_IOT_RA2_DIRECT_KEY_PEER_H
#include "ra2-rekey-peer-scope.h"
/* 1 exact retained ra2 peer; 0 no matching live MAC; -1 inconsistent/foreign.
 * A zero result is NOT authorization to treat a unicast request as group key. */
static inline int wr_ra2_direct_key_peer_locked(RTMP_ADAPTER *ad,
 const struct wr_ra2_rekey_peer_scope *scope,const unsigned char *addr,
 MAC_TABLE_ENTRY **result)
{
 unsigned int i;int foreign=0;
 MAC_TABLE_ENTRY *found=NULL;
 if(!result)return -1;
 *result=NULL;
 if(!ad||!scope||!scope->active||!addr||ad->wr_iot_peer_delete_active||
    !ad->wr_iot_peer_table_owner.transactions||
    !wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,0))return -1;
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[i];
  if(IS_ENTRY_NONE(entry)||!MAC_ADDR_EQUAL(entry->Addr,addr))continue;
  if(entry->wdev!=&ad->ApCfg.MBSSID[2].wdev){foreign=1;continue;}
  if(found||!IS_ENTRY_CLIENT(entry)||entry->func_tb_idx!=2||entry->wcid!=i||
     !scope->generations[i]||scope->generations[i]!=entry->assoc_gen||
     ad->wr_assoc_event_users[i]!=1)return -1;
  found=entry;
 }
 if(found){*result=found;return 1;}
 return foreign?-1:0;
}
#endif
