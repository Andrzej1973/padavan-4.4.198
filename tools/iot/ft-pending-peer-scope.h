/* A synchronous lease for a newly inserted first-peer FT request.
 * This helper is not wired into the SDK. The caller must own MacTabLock.
 * It binds the claimed BSS+MAC ticket to the exact newly published slot and
 * keeps association/delete/reset owners out until the native FT handler exits.
 */
#ifndef WR_IOT_FT_PENDING_PEER_SCOPE_H
#define WR_IOT_FT_PENDING_PEER_SCOPE_H

#include "ft-pending-identity.h"
#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include "assoc-generation.h"

static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *, MAC_TABLE_ENTRY *);

struct wr_ft_pending_peer_scope {
	RTMP_ADAPTER *adapter;
	unsigned int wcid;
	unsigned int generation;
	unsigned int bss;
	unsigned int active;
	unsigned char addr[MAC_ADDR_LEN];
};

static inline int wr_ft_pending_claimed_locked(
	const struct wr_ft_pending_ledger *ledger,
	const struct wr_ft_pending_token *token)
{
	unsigned int i;
	if (!ledger || !token || !token->generation ||
		token->slot >= WR_FT_PENDING_CAPACITY)
		return 0;
	i = token->slot;
	return ledger->state[i] == WR_FT_PENDING_CLAIMED &&
		ledger->generation[i] == token->generation &&
		ledger->references[i] &&
		wr_ft_pending_key_equal(ledger, i, token->bss, token->addr);
}

/* Reserve the free WCID before native entry initialization. The caller owns
 * MacTabLock and must either publish the initialized entry or cancel this
 * zero-generation reservation before unlocking on every native failure path.
 */
static inline int wr_ft_pending_peer_reserve_slot_locked(RTMP_ADAPTER *ad,
	unsigned int wcid, struct wifi_dev *wdev,
	const struct wr_ft_pending_token *ticket,
	struct wr_ft_pending_peer_scope *scope)
{
	unsigned int i;
	if (!ad || !wdev || !ticket || !scope || scope->active ||
		wcid == RESERVED_WCID || wcid >= MAX_LEN_OF_MAC_TABLE ||
		!wr_ft_pending_claimed_locked(&ad->wr_ft_pending, ticket) ||
		ticket->bss >= ad->ApCfg.BssidNum ||
		ticket->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
		wdev != &ad->ApCfg.MBSSID[ticket->bss].wdev ||
		wdev->func_idx != ticket->bss ||
		!IS_ENTRY_NONE(&ad->MacTab.Content[wcid]) ||
		ad->wr_assoc_event_users[wcid] ||
		ad->wr_assoc_generations[wcid] == ~0U ||
		!wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor) ||
		!wr_ft_pending_key_equal(&ad->wr_ft_pending, ticket->slot,
			ticket->bss, ticket->addr))
		return 0;
	if (!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))
		return 0;
	ad->wr_assoc_event_users[wcid] = 1;
	scope->adapter = ad;
	scope->wcid = wcid;
	scope->generation = 0;
	scope->bss = ticket->bss;
	scope->active = 1;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		scope->addr[i] = ticket->addr[i];
	return 1;
}

/* Complete a reservation only after the native entry generation is published.
 * Failure retains the reservation, poisons reset ownership and blocks deletion.
 */
static inline int wr_ft_pending_peer_publish_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry, const struct wr_ft_pending_token *ticket,
	struct wr_ft_pending_peer_scope *scope)
{
	unsigned int i, wcid;
	if (!ad || !entry || !ticket || !scope || !scope->active ||
		scope->adapter != ad || scope->generation ||
		!wr_ft_pending_claimed_locked(&ad->wr_ft_pending, ticket))
		goto uncertain;
	wcid = scope->wcid;
	if (wcid == RESERVED_WCID || wcid >= MAX_LEN_OF_MAC_TABLE ||
		entry != &ad->MacTab.Content[wcid] || !IS_ENTRY_CLIENT(entry) ||
		ad->wr_assoc_event_users[wcid] != 1 || !entry->assoc_gen ||
		entry->assoc_gen != ad->wr_assoc_generations[wcid] ||
		entry->assoc_gen != ad->wr_assoc_visible[wcid] ||
		entry->func_tb_idx != scope->bss ||
		scope->bss >= ad->ApCfg.BssidNum ||
		scope->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
		entry->wdev != &ad->ApCfg.MBSSID[scope->bss].wdev ||
		!wr_ft_pending_key_equal(&ad->wr_ft_pending, ticket->slot,
			ticket->bss, ticket->addr))
		goto uncertain;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (entry->Addr[i] != ticket->addr[i] ||
			scope->addr[i] != ticket->addr[i])
			goto uncertain;
	scope->generation = entry->assoc_gen;
	return 1;

uncertain:
	if (ad)
		ad->wr_iot_peer_table_owner.poisoned = 1;
	return 0;
}

/* Advance the association generation at the successful FT-auth transition.
 * Caller owns MacTabLock and still holds this exact peer lease. Existing
 * queued events retain the old generation and are rejected after publication.
 */
static inline int wr_ft_pending_peer_advance_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry, struct wr_ft_pending_peer_scope *scope)
{
	unsigned int i, wcid, generation;
	if (!ad || !entry || !scope || !scope->active || scope->adapter != ad)
		return 0;
	if (!scope->generation || scope->wcid == RESERVED_WCID ||
		scope->wcid >= MAX_LEN_OF_MAC_TABLE)
		goto uncertain;
	wcid = scope->wcid;
	if (entry != &ad->MacTab.Content[wcid] || !IS_ENTRY_CLIENT(entry) ||
		entry->wcid != wcid || entry->assoc_gen != scope->generation ||
		ad->wr_assoc_generations[wcid] != scope->generation ||
		ad->wr_assoc_visible[wcid] != scope->generation ||
		ad->wr_assoc_event_users[wcid] != 1 ||
		!ad->wr_iot_peer_table_owner.transactions ||
		entry->func_tb_idx != scope->bss ||
		scope->bss >= ad->ApCfg.BssidNum ||
		scope->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
		entry->wdev != &ad->ApCfg.MBSSID[scope->bss].wdev)
		goto uncertain;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (entry->Addr[i] != scope->addr[i])
			goto uncertain;
	generation = wr_assoc_generation_next(&ad->wr_assoc_generations[wcid]);
	if (!generation)
		goto uncertain;
	entry->assoc_gen = generation;
	wr_assoc_publish_slot_locked(ad, entry);
	scope->generation = generation;
	return 1;

uncertain:
	if (ad)
		ad->wr_iot_peer_table_owner.poisoned = 1;
	return 0;
}

/* Roll back only an unpublished reservation while its slot is still empty. */
static inline int wr_ft_pending_peer_cancel_slot_locked(RTMP_ADAPTER *ad,
	struct wr_ft_pending_peer_scope *scope)
{
	unsigned int wcid;
	if (!ad || !scope || !scope->active || scope->adapter != ad ||
		scope->generation || scope->wcid == RESERVED_WCID ||
		scope->wcid >= MAX_LEN_OF_MAC_TABLE)
		return 0;
	wcid = scope->wcid;
	if (!IS_ENTRY_NONE(&ad->MacTab.Content[wcid]) ||
		ad->wr_assoc_event_users[wcid] != 1 ||
		!ad->wr_iot_peer_table_owner.transactions) {
		ad->wr_iot_peer_table_owner.poisoned = 1;
		return 0;
	}
	ad->wr_assoc_event_users[wcid] = 0;
	scope->active = 0;
	scope->adapter = NULL;
	return wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner);
}

/* Call under MacTabLock before the native insertion critical section ends. */
static inline int wr_ft_pending_peer_enter_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry, const struct wr_ft_pending_token *ticket,
	struct wr_ft_pending_peer_scope *scope)
{
	unsigned int i, wcid;
	if (!ad || !entry || !ticket || !scope || scope->active ||
		!wr_ft_pending_claimed_locked(&ad->wr_ft_pending, ticket) ||
		ticket->bss >= ad->ApCfg.BssidNum ||
		ticket->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
		!wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor))
		return 0;
	wcid = entry->wcid;
	if (wcid == RESERVED_WCID || wcid >= MAX_LEN_OF_MAC_TABLE ||
		entry != &ad->MacTab.Content[wcid] || !IS_ENTRY_CLIENT(entry) ||
		!entry->assoc_gen || entry->func_tb_idx != ticket->bss ||
		ad->wr_assoc_generations[wcid] != entry->assoc_gen ||
		ad->wr_assoc_visible[wcid] != entry->assoc_gen ||
		entry->wdev != &ad->ApCfg.MBSSID[ticket->bss].wdev ||
		ad->wr_assoc_event_users[wcid] ||
		!wr_ft_pending_key_equal(&ad->wr_ft_pending, ticket->slot,
			ticket->bss, ticket->addr))
		return 0;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (entry->Addr[i] != ticket->addr[i])
			return 0;
	if (!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner))
		return 0;
	ad->wr_assoc_event_users[wcid] = 1;
	scope->adapter = ad;
	scope->wcid = wcid;
	scope->generation = entry->assoc_gen;
	scope->bss = ticket->bss;
	scope->active = 1;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		scope->addr[i] = ticket->addr[i];
	return 1;
}

/* Call under MacTabLock after the synchronous FT handler has returned.
 * Retain ownership and poison the table owner if slot identity drifted. */
static inline int wr_ft_pending_peer_leave_locked(RTMP_ADAPTER *ad,
	struct wr_ft_pending_peer_scope *scope)
{
	MAC_TABLE_ENTRY *entry;
	unsigned int i, wcid;
	if (!ad || !scope || !scope->active || scope->adapter != ad ||
		scope->wcid == RESERVED_WCID || scope->wcid >= MAX_LEN_OF_MAC_TABLE)
		return 0;
	if (ad->wr_iot_peer_table_owner.poisoned)
		return 0;
	wcid = scope->wcid;
	entry = &ad->MacTab.Content[wcid];
	if (ad->wr_assoc_event_users[wcid] != 1 || !IS_ENTRY_CLIENT(entry) ||
		entry->wcid != wcid || entry->assoc_gen != scope->generation ||
		ad->wr_assoc_generations[wcid] != scope->generation ||
		ad->wr_assoc_visible[wcid] != scope->generation ||
		entry->func_tb_idx != scope->bss ||
		scope->bss >= ad->ApCfg.BssidNum ||
		scope->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
		entry->wdev != &ad->ApCfg.MBSSID[scope->bss].wdev) {
		ad->wr_iot_peer_table_owner.poisoned = 1;
		return 0;
	}
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (entry->Addr[i] != scope->addr[i]) {
			ad->wr_iot_peer_table_owner.poisoned = 1;
			return 0;
		}
	if (!ad->wr_iot_peer_table_owner.transactions) {
		ad->wr_iot_peer_table_owner.poisoned = 1;
		return 0;
	}
	ad->wr_assoc_event_users[wcid] = 0;
	scope->active = 0;
	scope->adapter = NULL;
	return wr_iot_peer_table_transaction_leave(&ad->wr_iot_peer_table_owner);
}

#endif /* WR_IOT_FT_PENDING_PEER_SCOPE_H */
