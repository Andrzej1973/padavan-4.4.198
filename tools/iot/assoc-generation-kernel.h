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
/* Association success must invalidate an older queued handshake, even if the
 * WCID and MAC remain unchanged. Never hold this lock across WPA actions. */
static inline int wr_assoc_reassociate(RTMP_ADAPTER *ad, MAC_TABLE_ENTRY *entry)
{
 unsigned int generation = 0;
 if (!wr_assoc_try_table_lock(ad)) return 0;
 if (entry && entry->wcid < MAX_LEN_OF_MAC_TABLE && !IS_ENTRY_NONE(entry)) {
  generation = wr_assoc_generation_next(&ad->wr_assoc_generations[entry->wcid]);
  entry->assoc_gen = generation;
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
static inline struct wr_assoc_stamp wr_assoc_capture(RTMP_ADAPTER *ad,
 unsigned long machine, unsigned long len, void *msg, unsigned int wcid)
{
 struct wr_assoc_stamp stamp;
 MAC_TABLE_ENTRY *entry = NULL;
 unsigned char *addr = NULL;
 NdisZeroMemory(&stamp, sizeof(stamp));
 if (machine != WPA_STATE_MACHINE || !msg) return stamp;
 if (len == MAC_ADDR_LEN) addr = (unsigned char *)msg;
 else if (len >= LENGTH_802_11) addr = ((PHEADER_802_11)msg)->Addr2;
 if (!addr) return stamp;
 if (!wr_assoc_try_table_lock(ad)) return stamp;
 if (wcid == RESERVED_WCID) entry = MacTableLookup(ad, addr);
 else if (wcid < MAX_LEN_OF_MAC_TABLE) entry = &ad->MacTab.Content[wcid];
 if (entry && !IS_ENTRY_NONE(entry) && MAC_ADDR_EQUAL(entry->Addr, addr) &&
     entry->wcid < MAX_LEN_OF_MAC_TABLE && entry->assoc_gen) {
  stamp.gen = entry->assoc_gen;
  stamp.wcid = entry->wcid;
  COPY_MAC_ADDR(stamp.addr, entry->Addr);
 }
 NdisReleaseSpinLock(&ad->MacTabLock);
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
 MAC_TABLE_ENTRY *entry;
 int ok = 0;
 if (elem->Machine != WPA_STATE_MACHINE) return 1;
 if (elem->assoc_wcid >= MAX_LEN_OF_MAC_TABLE) return 0;
 if (!wr_assoc_try_table_lock(ad)) return 0;
 entry = &ad->MacTab.Content[elem->assoc_wcid];
 ok = wr_assoc_generation_matches(elem->assoc_gen, entry->assoc_gen,
  !IS_ENTRY_NONE(entry) && entry->wcid == elem->assoc_wcid,
  MAC_ADDR_EQUAL(elem->assoc_addr, entry->Addr));
 NdisReleaseSpinLock(&ad->MacTabLock);
 return ok;
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
