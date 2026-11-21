/* Prepared only. Transfer the existing AUTH peer reference to adapter-owned
 * identity while a response is CLAIMED; never duplicate or retain stack data.
 */
#ifndef WR_FT_IAPP_AUTH_OWNER_TRANSFER_H
#define WR_FT_IAPP_AUTH_OWNER_TRANSFER_H
#include "ft-auth-request-context.h"

/* Conservative probe used by AUTH cleanup. A malformed matching claim is
 * still owned work: callers must retain the stack scope and poison rather
 * than release its reference. */
static inline int wr_ft_iapp_auth_scope_claimed_locked(RTMP_ADAPTER *ad,
	const struct wr_ft_auth_request_context *context,
	struct wr_ft_iapp_request_state *state)
{
	struct wr_ft_peer_scope *existing;
	struct wr_ft_pending_peer_scope *pending;
	struct wr_ft_iapp_token_handle *request;
	struct wr_ft_iapp_token_entry *item;
	unsigned int w;
	if (!ad || !context || !state || state != &ad->wr_ft_iapp_requests)
		return 0;
	existing = context->existing;
	pending = context->pending;
	if (!!(existing && existing->active) == !!(pending && pending->active))
		return 0;
	w = existing && existing->active ? existing->stamp.wcid : pending->wcid;
	if (w == RESERVED_WCID || w >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    w >= MAX_LEN_OF_MAC_TABLE) return 0;
	request = &state->request_by_wcid[w];
	if (!request->serial) return 0;
	if (request->slot >= WR_FT_IAPP_TOKEN_CAPACITY) return 1;
	item = &state->ledger.entry[request->slot];
	return item->serial == request->serial &&
		item->state == WR_FT_IAPP_TOKEN_CLAIMED;
}

static inline int wr_ft_iapp_auth_hold_identity_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, unsigned int w)
{
	struct wr_ft_iapp_auth_owner_hold *hold;
	struct wr_ft_iapp_token_entry *item;
	MAC_TABLE_ENTRY *entry;
	if (!ad || !state || state != &ad->wr_ft_iapp_requests ||
	    w == RESERVED_WCID || w >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    w >= MAX_LEN_OF_MAC_TABLE)
		return 0;
	hold = &state->auth_hold[w];
	if (!hold->active || hold->wcid != w || !hold->generation ||
	    hold->bss >= ad->ApCfg.BssidNum ||
	    hold->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
	    !hold->request.serial || hold->request.slot >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    state->request_by_wcid[w].serial != hold->request.serial ||
	    state->request_by_wcid[w].slot != hold->request.slot ||
	    ad->wr_iot_peer_delete_active || ad->wr_iot_peer_table_owner.poisoned ||
	    !ad->wr_iot_peer_table_owner.transactions ||
	    ad->wr_assoc_event_users[w] != 1)
		return 0;
	item = &state->ledger.entry[hold->request.slot];
	entry = &ad->MacTab.Content[w];
	if (item->serial != hold->request.serial ||
	    (item->invalidated && item->state != WR_FT_IAPP_TOKEN_FREE) ||
	    item->bss != hold->bss || item->wcid != w ||
	    item->generation != hold->generation ||
	    !IS_ENTRY_CLIENT(entry) || entry->wcid != w ||
	    entry->func_tb_idx != hold->bss ||
	    entry->wdev != &ad->ApCfg.MBSSID[hold->bss].wdev ||
	    (entry->Sst != SST_NOT_AUTH && entry->Sst != SST_AUTH &&
	     entry->Sst != SST_ASSOC) ||
	    entry->assoc_gen != hold->generation ||
	    ad->wr_assoc_generations[w] != hold->generation ||
	    ad->wr_assoc_visible[w] != hold->generation ||
	    (entry->Sst != SST_NOT_AUTH && entry->Sst != SST_AUTH &&
	     entry->Sst != SST_ASSOC) ||
	    __builtin_memcmp(entry->Addr, item->mac, MAC_ADDR_LEN) ||
	    __builtin_memcmp(entry->Addr, hold->mac, MAC_ADDR_LEN) ||
	    __builtin_memcmp(ad->wr_assoc_addr[w], hold->mac, MAC_ADDR_LEN) ||
	    __builtin_memcmp(ad->ApCfg.MBSSID[hold->bss].wdev.bssid, item->bssid,
		MAC_ADDR_LEN))
		return 0;
	return 1;
}

static inline int wr_ft_iapp_auth_hold_release_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, unsigned int w);

/* After response unclaim, adopt the exact request as a detached WAITING
 * retry before releasing the transferred peer reference. */
static inline int wr_ft_iapp_auth_hold_detach_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, unsigned int w)
{
	struct wr_ft_iapp_auth_owner_hold *hold;
	struct wr_ft_iapp_token_entry *item;
	MAC_TABLE_ENTRY *entry;
	unsigned int i;
	if (!wr_ft_iapp_auth_hold_identity_locked(ad, state, w)) return 0;
	hold = &state->auth_hold[w];
	item = &state->ledger.entry[hold->request.slot];
	entry = &ad->MacTab.Content[w];
	if (item->state != WR_FT_IAPP_TOKEN_WAITING || item->invalidated ||
	    state->detached[w] || state->request_by_wcid[w].serial != hold->request.serial ||
	    state->request_by_wcid[w].slot != hold->request.slot)
		return 0;
	state->detached[w] = 1;
	state->detached_sst[w] = entry->Sst;
	if (hold->pending) {
		struct wr_ft_preauth_identity *identity = &state->preauth[w];
		identity->serial = hold->request.serial;
		identity->generation = hold->generation;
		identity->bss = hold->bss;
		identity->wcid = w;
		for (i = 0; i < MAC_ADDR_LEN; i++) {
			identity->mac[i] = hold->mac[i];
			identity->bssid[i] = ad->ApCfg.MBSSID[hold->bss].wdev.bssid[i];
		}
	}
	if (!wr_ft_iapp_auth_hold_release_locked(ad, state, w)) {
		state->detached[w] = 0;
		state->detached_sst[w] = 0;
		if (hold->pending) state->preauth[w] = (struct wr_ft_preauth_identity){0};
		return 0;
	}
	return 1;
}

/* Called at AUTH exit under MacTabLock. On success the caller's scope becomes
 * inactive without decrementing the one reference or table transaction. */
static inline int wr_ft_iapp_auth_hold_claimed_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry, const struct wr_ft_auth_request_context *context,
	struct wr_ft_iapp_request_state *state)
{
	struct wr_ft_iapp_auth_owner_hold *hold;
	struct wr_ft_peer_scope *existing;
	struct wr_ft_pending_peer_scope *pending;
	struct wr_ft_iapp_token_handle request;
	struct wr_ft_iapp_token_entry *item;
	unsigned int w, i;
	if (!ad || !entry || !state || !context ||
	    !wr_ft_auth_request_current_locked(ad, entry, context))
		return 0;
	existing = context->existing;
	pending = context->pending;
	w = entry->wcid;
	if (w == RESERVED_WCID || w >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    w >= MAX_LEN_OF_MAC_TABLE || state->detached[w] ||
	    state->auth_hold[w].active || !state->request_by_wcid[w].serial ||
	    state->request_by_wcid[w].slot >= WR_FT_IAPP_TOKEN_CAPACITY)
		return 0;
	request = state->request_by_wcid[w];
	item = &state->ledger.entry[request.slot];
	if (item->state != WR_FT_IAPP_TOKEN_CLAIMED || item->invalidated ||
	    item->serial != request.serial || item->wcid != w ||
	    item->bss != entry->func_tb_idx || item->generation != entry->assoc_gen ||
	    ad->wr_assoc_event_users[w] != 1 ||
	    !ad->wr_iot_peer_table_owner.transactions)
		return 0;
	if (existing) {
		if (!existing->active || existing->adapter != ad ||
		    existing->stamp.wcid != w ||
		    existing->stamp.bss != item->bss ||
		    existing->stamp.generation != item->generation)
			return 0;
		for (i = 0; i < MAC_ADDR_LEN; i++)
			if (existing->stamp.addr[i] != item->mac[i]) return 0;
	} else if (pending) {
		if (!pending->active || pending->adapter != ad ||
		    pending->wcid != w || pending->bss != item->bss ||
		    pending->generation != item->generation)
			return 0;
		for (i = 0; i < MAC_ADDR_LEN; i++)
			if (pending->addr[i] != item->mac[i]) return 0;
	} else return 0;
	hold = &state->auth_hold[w];
	hold->request = request;
	hold->active = 1;
	hold->pending = pending && pending->active;
	hold->generation = item->generation;
	hold->bss = item->bss;
	hold->wcid = w;
	for (i = 0; i < MAC_ADDR_LEN; i++) hold->mac[i] = item->mac[i];
	if (existing) { existing->active = 0; existing->adapter = NULL; }
	else { pending->active = 0; pending->adapter = NULL; }
	return 1;
}

/* The response callback owns MacTabLock. Construct a temporary exact scope to
 * reuse the established validators and consume the transferred reference. */
static inline int wr_ft_iapp_auth_hold_release_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, unsigned int w)
{
	struct wr_ft_iapp_auth_owner_hold *hold;
	int released;
	if (!wr_ft_iapp_auth_hold_identity_locked(ad, state, w)) return 0;
	hold = &state->auth_hold[w];
	if (hold->pending) {
		struct wr_ft_pending_peer_scope scope = {0};
		scope.adapter = ad; scope.wcid = w; scope.generation = hold->generation;
		scope.bss = hold->bss; scope.active = 1;
		__builtin_memcpy(scope.addr, hold->mac, MAC_ADDR_LEN);
		released = wr_ft_pending_peer_leave_locked(ad, &scope);
	} else {
		struct wr_ft_peer_scope scope = {0};
		scope.adapter = ad; scope.stamp.wcid = w; scope.stamp.bss = hold->bss;
		scope.stamp.generation = hold->generation; scope.active = 1;
		__builtin_memcpy(scope.stamp.addr, hold->mac, MAC_ADDR_LEN);
		released = wr_ft_peer_leave_locked(ad, &scope);
	}
	if (!released) {
		ad->wr_iot_peer_table_owner.poisoned = 1;
		return 0;
	}
	*hold = (struct wr_ft_iapp_auth_owner_hold){0};
	return 1;
}

#endif
