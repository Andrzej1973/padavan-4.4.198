/* Prepared FT existing-peer identity and synchronous lease. Not installed.
 * Caller owns MacTabLock on every call and adapter/BSS lifetime throughout.
 * Caller must separately hold association-vs-key/control admission over native
 * work. Scopes are private linear stack values; never copy an active scope.
 * Generation advances only through the explicit success-boundary helper.
 * No lock, queue operation or crypto runs here. */
#ifndef WR_IOT_FT_PEER_GENERATION_H
#define WR_IOT_FT_PEER_GENERATION_H
#include "assoc-generation.h"
#include "peer-table-owner.h"
struct wr_ft_peer_stamp {
 unsigned int generation,wcid,bss;
 unsigned char addr[MAC_ADDR_LEN];
};
struct wr_ft_peer_scope {
 RTMP_ADAPTER *adapter;
 struct wr_ft_peer_stamp stamp;
 unsigned int active;
};
static inline int wr_ft_peer_current_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_peer_stamp *stamp)
{
 MAC_TABLE_ENTRY *entry;
 if(!ad||!stamp||!stamp->generation||stamp->wcid==RESERVED_WCID||
  stamp->wcid>=MAX_LEN_OF_MAC_TABLE||stamp->bss>=ad->ApCfg.BssidNum||
  stamp->bss>=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))return 0;
 entry=&ad->MacTab.Content[stamp->wcid];
 return IS_ENTRY_CLIENT(entry)&&entry->wcid==stamp->wcid&&
  (entry->Sst==SST_AUTH||entry->Sst==SST_ASSOC)&&
  entry->func_tb_idx==stamp->bss&&
  entry->wdev==&ad->ApCfg.MBSSID[stamp->bss].wdev&&
  entry->assoc_gen==stamp->generation&&
  MAC_ADDR_EQUAL(entry->Addr,stamp->addr);
}
static inline int wr_ft_peer_capture_locked(RTMP_ADAPTER *ad,
 unsigned int wcid,unsigned int bss,const unsigned char *addr,
 struct wr_ft_peer_stamp *out)
{
 struct wr_ft_peer_stamp captured={0};
 unsigned int i;
 if(!out)return 0;
 *out=captured;
 if(!ad||!addr||wcid==RESERVED_WCID||wcid>=MAX_LEN_OF_MAC_TABLE)return 0;
 captured.wcid=wcid;captured.bss=bss;
 captured.generation=ad->MacTab.Content[wcid].assoc_gen;
 for(i=0;i<MAC_ADDR_LEN;i++)captured.addr[i]=addr[i];
 if(!wr_ft_peer_current_locked(ad,&captured))return 0;
 *out=captured;return 1;
}
static inline int wr_ft_peer_enter_locked(RTMP_ADAPTER *ad,
 const struct wr_ft_peer_stamp *stamp,struct wr_ft_peer_scope *scope)
{
 if(!scope||scope->active||!wr_ft_peer_current_locked(ad,stamp)||
  ad->wr_iot_peer_delete_active||ad->wr_assoc_event_users[stamp->wcid])return 0;
 if(!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))return 0;
 scope->adapter=ad;scope->stamp=*stamp;scope->active=1;
 ad->wr_assoc_event_users[stamp->wcid]=1;
	return 1;
}
/* Call at the successful native FT-auth transition while MacTabLock and this
 * exact peer lease are still held. Earlier queued stamps become stale; the
 * scope adopts the new generation so it can be released without rebinding.
 */
static inline int wr_ft_peer_advance_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry, struct wr_ft_peer_scope *scope)
{
	unsigned int i, wcid, generation;
	if (!ad || !entry || !scope || !scope->active || scope->adapter != ad)
		return 0;
	wcid = scope->stamp.wcid;
	if (!wr_ft_peer_current_locked(ad, &scope->stamp) ||
		entry != &ad->MacTab.Content[wcid] ||
		ad->wr_assoc_event_users[wcid] != 1 ||
		!ad->wr_iot_peer_table_owner.transactions ||
		ad->wr_assoc_generations[wcid] != scope->stamp.generation ||
		ad->wr_assoc_visible[wcid] != scope->stamp.generation)
		goto uncertain;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (ad->wr_assoc_addr[wcid][i] != scope->stamp.addr[i])
			goto uncertain;
	generation = wr_assoc_generation_next(&ad->wr_assoc_generations[wcid]);
	if (!generation)
		goto uncertain;
	entry->assoc_gen = generation;
	WRITE_ONCE(ad->wr_assoc_visible[wcid], 0);
	smp_wmb();
	for (i = 0; i < MAC_ADDR_LEN; i++)
		WRITE_ONCE(ad->wr_assoc_addr[wcid][i], entry->Addr[i]);
	smp_wmb();
	WRITE_ONCE(ad->wr_assoc_visible[wcid], generation);
	scope->stamp.generation = generation;
	return 1;

uncertain:
	ad->wr_iot_peer_table_owner.poisoned = 1;
	return 0;
}
static inline int wr_ft_peer_leave_locked(RTMP_ADAPTER *ad,
 struct wr_ft_peer_scope *scope)
{
 unsigned int wcid;
 if(!ad||!scope||!scope->active||scope->adapter!=ad)return 0;
 if(ad->wr_iot_peer_table_owner.poisoned)return 0;
 wcid=scope->stamp.wcid;
 if(!wr_ft_peer_current_locked(ad,&scope->stamp)||
  ad->wr_assoc_event_users[wcid]!=1){
  ad->wr_iot_peer_table_owner.poisoned=1;
  return 0; /* Retain uncertain ownership; never release a different peer. */
 }
 ad->wr_assoc_event_users[wcid]=0;
 scope->active=0;scope->adapter=0;
 return wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner);
}
#endif
