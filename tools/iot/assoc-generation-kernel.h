#ifndef WR_IOT_ASSOC_GENERATION_KERNEL_H
#define WR_IOT_ASSOC_GENERATION_KERNEL_H
#include "assoc-generation.h"
/* Native deletion cancels station timers while owning MacTabLock. A callback
 * must not wait for that lock and form cancel-timer <-> table-lock deadlock.
 * Match the SDK's direct/OS_ABL lock representation and BH lock semantics. */
static inline int wr_assoc_try_table_lock(RTMP_ADAPTER *ad)
{
#ifdef OS_ABL_FUNC_SUPPORT
 if (!ad->MacTabLock.pContent) return 0;
 return spin_trylock_bh((spinlock_t *)ad->MacTabLock.pContent);
#else
 return spin_trylock_bh(&ad->MacTabLock);
#endif
}
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *,MAC_TABLE_ENTRY *);
/* Association success must invalidate an older queued handshake, even if the
 * WCID and MAC remain unchanged. Never hold this lock across WPA actions. */
static inline int wr_assoc_reassociate(RTMP_ADAPTER *ad, MAC_TABLE_ENTRY *entry)
{
 unsigned int generation = 0;
 if (!wr_assoc_try_table_lock(ad)) return 0;
 if (entry && entry->wcid < MAX_LEN_OF_MAC_TABLE && !IS_ENTRY_NONE(entry) &&
     !ad->wr_assoc_event_users[entry->wcid]) {
  generation = wr_assoc_generation_next(&ad->wr_assoc_generations[entry->wcid]);
  entry->assoc_gen = generation;
  wr_assoc_publish_slot_locked(ad,entry);
 }
 NdisReleaseSpinLock(&ad->MacTabLock);
 return generation != 0;
}
/* Caller already owns MacTabLock, including native insertion/deletion. */
static inline unsigned int wr_assoc_advance_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry, unsigned int wcid)
{
 if (wcid >= MAX_LEN_OF_MAC_TABLE) return 0;
 entry->assoc_gen = wr_assoc_generation_next(&ad->wr_assoc_generations[wcid]);
 return entry->assoc_gen;
}
struct wr_assoc_stamp {
 unsigned int gen;
 unsigned short wcid;
 unsigned char addr[MAC_ADDR_LEN];
};
/* Identity publication is separate from the mutable/cleared entry. Writers
 * own MacTabLock. Zero withdraws publication; a nonzero generation never repeats.
 * Readers are bounded and never wait for a table owner cancelling their timer. */
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,
 MAC_TABLE_ENTRY *entry)
{
 unsigned int i, slot=entry->wcid;
 if (slot >= MAX_LEN_OF_MAC_TABLE) return;
 WRITE_ONCE(ad->wr_assoc_visible[slot],0);
 smp_wmb();
 for(i=0;i<MAC_ADDR_LEN;i++) WRITE_ONCE(ad->wr_assoc_addr[slot][i],entry->Addr[i]);
 smp_wmb();
 WRITE_ONCE(ad->wr_assoc_visible[slot],entry->assoc_gen);
}
static inline struct wr_assoc_stamp wr_assoc_read_slot(RTMP_ADAPTER *ad,
 unsigned int slot, const unsigned char *addr)
{
 struct wr_assoc_stamp stamp;
 unsigned int generation,i;
 NdisZeroMemory(&stamp,sizeof(stamp));
 if (slot >= MAX_LEN_OF_MAC_TABLE) return stamp;
 generation=READ_ONCE(ad->wr_assoc_visible[slot]);
 if (!generation) return stamp;
 smp_rmb();
 for(i=0;i<MAC_ADDR_LEN;i++) stamp.addr[i]=READ_ONCE(ad->wr_assoc_addr[slot][i]);
 smp_rmb();
 if (generation!=READ_ONCE(ad->wr_assoc_visible[slot]) ||
     generation!=READ_ONCE(ad->MacTab.Content[slot].assoc_gen) ||
     IS_ENTRY_NONE(&ad->MacTab.Content[slot]) ||
     READ_ONCE(ad->MacTab.Content[slot].wcid)!=slot ||
     !MAC_ADDR_EQUAL(stamp.addr,addr)) {
  NdisZeroMemory(&stamp,sizeof(stamp));return stamp;
 }
 for(i=0;i<MAC_ADDR_LEN;i++) if(stamp.addr[i]!=READ_ONCE(ad->MacTab.Content[slot].Addr[i])) {
  NdisZeroMemory(&stamp,sizeof(stamp));return stamp;
 }
 smp_rmb();
 if(generation!=READ_ONCE(ad->wr_assoc_visible[slot])) {
  NdisZeroMemory(&stamp,sizeof(stamp));return stamp;
 }
 stamp.gen=generation;stamp.wcid=slot;return stamp;
}
static inline struct wr_assoc_stamp wr_assoc_capture(RTMP_ADAPTER *ad,
 unsigned long machine, unsigned long len, void *msg, unsigned int wcid)
{
 struct wr_assoc_stamp stamp;
 unsigned char *addr=NULL;
 unsigned int i;
 NdisZeroMemory(&stamp,sizeof(stamp));
 if (machine!=WPA_STATE_MACHINE || !msg) return stamp;
 if (len==MAC_ADDR_LEN) addr=(unsigned char *)msg;
 else if (len>=LENGTH_802_11) addr=((PHEADER_802_11)msg)->Addr2;
 if (!addr) return stamp;
 if (wcid!=RESERVED_WCID) return wr_assoc_read_slot(ad,wcid,addr);
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++) {
  stamp=wr_assoc_read_slot(ad,i,addr);
  if(stamp.gen) return stamp;
 }
 return stamp;
}
static inline void wr_assoc_publish(MLME_QUEUE_ELEM *elem,
 const struct wr_assoc_stamp *stamp)
{
 elem->assoc_gen = stamp->gen;
 elem->assoc_wcid = stamp->wcid;
 COPY_MAC_ADDR(elem->assoc_addr, stamp->addr);
}
static inline int wr_assoc_event_current(RTMP_ADAPTER *ad, MLME_QUEUE_ELEM *elem)
{
 struct wr_assoc_stamp observed;
 if (elem->Machine!=WPA_STATE_MACHINE) return 1;
 observed=wr_assoc_read_slot(ad,elem->assoc_wcid,elem->assoc_addr);
 return wr_assoc_generation_matches(elem->assoc_gen,observed.gen,
  observed.gen!=0,observed.wcid==elem->assoc_wcid);
}
/* Native action lookups must resolve to the stamped slot, not a same-MAC
 * peer in another BSS. Still a point-in-time validation, not a reference pin. */
static inline int wr_assoc_event_entry_current(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *elem, MAC_TABLE_ENTRY *entry)
{
 return elem->assoc_wcid < MAX_LEN_OF_MAC_TABLE &&
  entry == &ad->MacTab.Content[elem->assoc_wcid] &&
  wr_assoc_event_current(ad, elem);
}
#endif
