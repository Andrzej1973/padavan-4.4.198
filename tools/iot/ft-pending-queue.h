/* Uninstalled linear ticket transport. Queue->Lock protects publication;
 * consumer exclusively owns a dequeued occupied element before take.
 * No table lock, refcount change, generation capture or native dispatch here.
 * take transfers ownership to a local token; that owner MUST release it under
 * MacTabLock, including stale/drop paths. Never clear a live element first.
 */
#ifndef WR_IOT_FT_PENDING_QUEUE_H
#define WR_IOT_FT_PENDING_QUEUE_H
#include "ft-pending-identity.h"

static inline void wr_ft_pending_elem_init(MLME_QUEUE_ELEM *elem)
{
 unsigned int i;
 elem->ft_pending_generation=0;elem->ft_pending_slot=0;elem->ft_pending_bss=0;
 for(i=0;i<MAC_ADDR_LEN;i++)elem->ft_pending_addr[i]=0;
}

static inline int wr_ft_pending_elem_publish(MLME_QUEUE_ELEM *elem,
	struct wr_ft_pending_token *token)
{
 unsigned int i;
 if(!elem||!token||!token->generation||elem->ft_pending_generation)return 0;
 elem->ft_pending_slot=token->slot;elem->ft_pending_bss=token->bss;
 for(i=0;i<MAC_ADDR_LEN;i++)elem->ft_pending_addr[i]=token->addr[i];
 elem->ft_pending_generation=token->generation;
 wr_ft_pending_token_clear(token);
	return 1;
}

/* Snapshot without consuming the queue's reference. Intended for a handler
 * that must claim the identity while the MLME dispatcher remains release owner.
 */
static inline int wr_ft_pending_elem_snapshot(const MLME_QUEUE_ELEM *elem,
	struct wr_ft_pending_token *token)
{
	unsigned int i;
	if (!elem || !token || token->generation || !elem->ft_pending_generation)
		return 0;
	token->slot = elem->ft_pending_slot;
	token->bss = elem->ft_pending_bss;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		token->addr[i] = elem->ft_pending_addr[i];
	token->generation = elem->ft_pending_generation;
	return 1;
}

static inline int wr_ft_pending_elem_take(MLME_QUEUE_ELEM *elem,
 struct wr_ft_pending_token *token)
{
 unsigned int i;
 if(!elem||!token||token->generation||!elem->ft_pending_generation)return 0;
 token->slot=elem->ft_pending_slot;token->bss=elem->ft_pending_bss;
 for(i=0;i<MAC_ADDR_LEN;i++)token->addr[i]=elem->ft_pending_addr[i];
 token->generation=elem->ft_pending_generation;
 wr_ft_pending_elem_init(elem);
 return 1;
}

/* Called while the owning queue lock is held, before Occupied is cleared.
 * The returned value owns the queue's single reference and must be released
 * after dropping Queue->Lock. */
static inline int wr_ft_pending_elem_detach(MLME_QUEUE_ELEM *elem,
 struct wr_ft_pending_token *token)
{
 return wr_ft_pending_elem_take(elem,token);
}

/* Caller owns MacTabLock and the detached/exclusive element. */
static inline int wr_ft_pending_elem_release_locked(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *elem)
{
 struct wr_ft_pending_token token={0};
 if(!wr_ft_pending_elem_take(elem,&token))return 0;
 return wr_ft_pending_release_locked(&ad->wr_ft_pending,&token);
}

/* Element is exclusively owned by the dispatcher or has been detached from
 * its queue. Caller must not hold Queue->Lock while this acquires MacTabLock. */
static inline int wr_ft_pending_elem_release(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *elem)
{
 struct wr_ft_pending_token token={0};
 int released;
 if(!wr_ft_pending_elem_take(elem,&token))return 0;
 NdisAcquireSpinLock(&ad->MacTabLock);
 released=wr_ft_pending_release_locked(&ad->wr_ft_pending,&token);
 NdisReleaseSpinLock(&ad->MacTabLock);
 return released;
}
#endif
