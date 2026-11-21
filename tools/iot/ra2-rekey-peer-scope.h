/* Caller already owns the ra2 key arbiter and adapter/control lifetime.
 * All native ra2 insertion/auth/association actors must use that arbiter.
 * This scope pins table entries only; it is not a DMA/firmware receipt. */
#ifndef WR_IOT_RA2_REKEY_PEER_SCOPE_H
#define WR_IOT_RA2_REKEY_PEER_SCOPE_H
#include "assoc-generation-kernel.h"
#include "peer-table-owner.h"
struct wr_ra2_rekey_peer_scope {
 unsigned int active;
 unsigned int generations[MAX_LEN_OF_MAC_TABLE];
};
static inline int wr_ra2_rekey_peers_enter(RTMP_ADAPTER *ad,
 struct wr_ra2_rekey_peer_scope *scope)
{
 unsigned int i;
 NdisZeroMemory(scope,sizeof(*scope));
 if(!wr_assoc_try_table_lock(ad))return 0;
 /* An earlier insertion may still own its unlocked tail. Refuse before any
  * mutation rather than race it; natural periodic rearm owns the next try. */
 if(ad->wr_iot_peer_delete_active||ad->wr_iot_peer_table_owner.transactions||
    !wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,0))goto refuse;
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[i];
  if(IS_ENTRY_NONE(entry))continue;
  if(entry->wdev!=&ad->ApCfg.MBSSID[2].wdev){
   if(IS_ENTRY_CLIENT(entry)&&entry->func_tb_idx==2)goto refuse;
   continue; /* A WDS/APCLI index 2 is not the ra2 client BSS. */
  }
  if(!IS_ENTRY_CLIENT(entry)||entry->func_tb_idx!=2||
     entry->wcid!=i||!entry->assoc_gen||ad->wr_assoc_event_users[i])goto refuse;
 }
 if(!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))goto refuse;
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[i];
  if(!IS_ENTRY_NONE(entry)&&entry->wdev==&ad->ApCfg.MBSSID[2].wdev){
   scope->generations[i]=entry->assoc_gen;
   ad->wr_assoc_event_users[i]=1;
  }
 }
 scope->active=1;
 NdisReleaseSpinLock(&ad->MacTabLock);return 1;
refuse:
 NdisReleaseSpinLock(&ad->MacTabLock);return 0;
}
static inline int wr_ra2_rekey_peers_leave(RTMP_ADAPTER *ad,
 struct wr_ra2_rekey_peer_scope *scope)
{
 unsigned int i;int valid=1;
 if(!scope->active)return 0;
 NdisAcquireSpinLock(&ad->MacTabLock);
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[i];
  if(!scope->generations[i])continue;
  if(ad->wr_assoc_event_users[i]!=1||entry->assoc_gen!=scope->generations[i]||
     !IS_ENTRY_CLIENT(entry)||entry->func_tb_idx!=2||entry->wcid!=i||
     entry->wdev!=&ad->ApCfg.MBSSID[2].wdev)valid=0;
  else ad->wr_assoc_event_users[i]=0;
 }
 if(!wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner))valid=0;
 if(!valid)ad->wr_iot_peer_table_owner.poisoned=1;
 scope->active=0;
 NdisReleaseSpinLock(&ad->MacTabLock);return valid;
}
#endif
