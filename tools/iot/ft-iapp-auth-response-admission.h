/* Prepared only. Borrows the exact live AUTH owner; it does not create a
 * second peer reference or return an entry pointer. Claim under MacTabLock,
 * drop that lock for the separately leased native cache operation, then
 * reacquire it and call finish after counters/ACK. The CLAIMED token and AUTH
 * peer lease prevent timeout/reassociation/deletion between the phases.
 * Detached retries use the separate detached-response owner and are refused.
 */
#ifndef WR_FT_IAPP_AUTH_RESPONSE_ADMISSION_H
#define WR_FT_IAPP_AUTH_RESPONSE_ADMISSION_H

#include "ft-iapp-peer-admission.h"
#include "ft-iapp-request-state.h"
#include "ft-iapp-auth-owner-transfer.h"

struct wr_ft_iapp_auth_response {
	RTMP_ADAPTER *adapter;
	struct wr_ft_iapp_request_state *state;
	struct wr_ft_peer_stamp peer;
	struct wr_ft_iapp_token_handle request;
	struct wr_ft_iapp_token_handle response;
	unsigned int active;
};

/* Validate the live AUTH lease from its published request identity. A first
 * FT peer may still be SST_NOT_AUTH while the pending insertion scope owns the
 * one event reference; established peers are AUTH or ASSOC. */
static inline int wr_ft_iapp_auth_request_owner_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state,
	const struct wr_ft_iapp_token_handle *request)
{
	const struct wr_ft_iapp_token_entry *item;
	MAC_TABLE_ENTRY *entry;
	unsigned int w;
	if (!ad || !state || state != &ad->wr_ft_iapp_requests || !request ||
	    !request->serial || request->slot >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    state->ledger.poisoned || ad->wr_iot_peer_delete_active ||
	    ad->wr_iot_peer_table_owner.poisoned ||
	    !ad->wr_iot_peer_table_owner.transactions)
		return 0;
	w = state->ledger.entry[request->slot].wcid;
	if (w == RESERVED_WCID || w >= WR_FT_IAPP_TOKEN_CAPACITY ||
	    w >= MAX_LEN_OF_MAC_TABLE || state->detached[w] ||
	    state->request_by_wcid[w].serial != request->serial ||
	    state->request_by_wcid[w].slot != request->slot ||
	    ad->wr_assoc_event_users[w] != 1)
		return 0;
	if (state->auth_hold[w].active)
		return wr_ft_iapp_auth_hold_identity_locked(ad, state, w);
	item = &state->ledger.entry[request->slot];
	entry = &ad->MacTab.Content[w];
	if (item->serial != request->serial || item->invalidated ||
	    (item->state != WR_FT_IAPP_TOKEN_WAITING &&
	     item->state != WR_FT_IAPP_TOKEN_CLAIMED) ||
	    !item->generation || item->bss >= ad->ApCfg.BssidNum ||
	    item->bss >= sizeof(ad->ApCfg.MBSSID) / sizeof(ad->ApCfg.MBSSID[0]) ||
	    !IS_ENTRY_CLIENT(entry) || entry->wcid != w ||
	    entry->func_tb_idx != item->bss ||
	    entry->wdev != &ad->ApCfg.MBSSID[item->bss].wdev ||
	    (entry->Sst != SST_NOT_AUTH && entry->Sst != SST_AUTH &&
	     entry->Sst != SST_ASSOC) ||
	    entry->assoc_gen != item->generation ||
	    ad->wr_assoc_generations[w] != item->generation ||
	    ad->wr_assoc_visible[w] != item->generation ||
	    __builtin_memcmp(entry->Addr, item->mac, MAC_ADDR_LEN) ||
	    __builtin_memcmp(ad->wr_assoc_addr[w], item->mac, MAC_ADDR_LEN) ||
	    __builtin_memcmp(ad->ApCfg.MBSSID[item->bss].wdev.bssid,
		item->bssid, MAC_ADDR_LEN))
		return 0;
	return 1;
}

static inline int wr_ft_iapp_auth_response_enter_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, const unsigned char *token,
	const unsigned char *mac, const unsigned char *bssid,
	struct wr_ft_iapp_auth_response *owner)
{
	unsigned int i, j, w;
	struct wr_ft_iapp_token_entry *request;
	struct wr_ft_peer_stamp stamp = {0};
	struct wr_ft_iapp_token_handle claimed = {0};
	if (!ad || !state || state != &ad->wr_ft_iapp_requests || !token ||
	    !mac || !bssid || !owner || owner->active ||
	    state->ledger.poisoned ||
	    !wr_ft_iapp_token_nonzero(token))
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		request = &state->ledger.entry[i];
		if (request->state != WR_FT_IAPP_TOKEN_WAITING || !request->serial ||
		    request->invalidated || !wr_ft_iapp_token_equal(request->token, token) ||
		    __builtin_memcmp(request->mac, mac, MAC_ADDR_LEN) ||
		    __builtin_memcmp(request->bssid, bssid, MAC_ADDR_LEN))
			continue;
		w = request->wcid;
		if (w == RESERVED_WCID || w >= WR_FT_IAPP_TOKEN_CAPACITY ||
		    w >= MAX_LEN_OF_MAC_TABLE || state->detached[w] ||
		    state->request_by_wcid[w].serial != request->serial ||
		    state->request_by_wcid[w].slot != i)
			return 0;
		stamp.wcid = w;
		stamp.bss = request->bss;
		stamp.generation = request->generation;
		for (j = 0; j < MAC_ADDR_LEN; j++)
			stamp.addr[j] = request->mac[j];
		if (!wr_ft_iapp_auth_request_owner_locked(ad, state,
				&state->request_by_wcid[w]) ||
		    !wr_ft_iapp_token_claim_context_locked(&state->ledger, token,
				mac, bssid, stamp.bss, stamp.wcid, stamp.generation,
				stamp.addr, ad->ApCfg.MBSSID[stamp.bss].wdev.bssid,
				&claimed))
			return 0;
		owner->adapter = ad;
		owner->state = state;
		owner->peer = stamp;
		owner->request = state->request_by_wcid[w];
		owner->response = claimed;
		owner->active = 1;
		return 1;
	}
	return 0;
}

/* Native IAPP replies carry the request token and station MAC, but not our
 * BSSID. Derive the interface only from the unique live token ledger entry;
 * never infer it by searching the client table for the MAC. */
static inline int wr_ft_iapp_auth_response_enter_token_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_request_state *state, const unsigned char *token,
	const unsigned char *mac, struct wr_ft_iapp_auth_response *owner)
{
	struct wr_ft_iapp_token_entry *request = NULL;
	unsigned int i;
	if (!ad || !state || state != &ad->wr_ft_iapp_requests || !token ||
	    !mac || !owner || owner->active || state->ledger.poisoned ||
	    !wr_ft_iapp_token_nonzero(token))
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *item = &state->ledger.entry[i];
		if (item->state == WR_FT_IAPP_TOKEN_FREE ||
		    !wr_ft_iapp_token_equal(item->token, token))
			continue;
		/* Duplicate token bytes or an invalid lifecycle state are ambiguous. */
		if (request || item->state != WR_FT_IAPP_TOKEN_WAITING ||
		    !item->serial || item->invalidated)
			return 0;
		request = item;
	}
	if (!request || __builtin_memcmp(request->mac, mac, MAC_ADDR_LEN) ||
	    request->bss >= ad->ApCfg.BssidNum ||
	    request->bss >= sizeof(ad->ApCfg.MBSSID) /
					   sizeof(ad->ApCfg.MBSSID[0]))
		return 0;
	return wr_ft_iapp_auth_response_enter_locked(ad, state, token, mac,
		ad->ApCfg.MBSSID[request->bss].wdev.bssid, owner);
}

/* Called only after cache, retry-counter and optional ACK completion work.
 * Any identity/ownership drift retains the claimed response and AUTH owner.
 */
static inline int wr_ft_iapp_auth_response_finish_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_auth_response *owner)
{
	unsigned int w;
	struct wr_ft_iapp_token_entry *response;
	if (!ad || !owner || !owner->active || owner->adapter != ad ||
	    owner->state != &ad->wr_ft_iapp_requests)
		return 0;
	w = owner->peer.wcid;
	if (w >= WR_FT_IAPP_TOKEN_CAPACITY || w >= MAX_LEN_OF_MAC_TABLE ||
	    !wr_ft_iapp_auth_request_owner_locked(ad, owner->state,
			&owner->request) ||
	    ad->wr_ft_iapp_requests.request_by_wcid[w].serial != owner->request.serial ||
	    ad->wr_ft_iapp_requests.request_by_wcid[w].slot != owner->request.slot ||
	    owner->response.slot >= WR_FT_IAPP_TOKEN_CAPACITY)
		return 0;
	response = &owner->state->ledger.entry[owner->response.slot];
	if (response->state != WR_FT_IAPP_TOKEN_CLAIMED || response->invalidated ||
	    response->serial != owner->response.serial ||
	    response->bss != owner->peer.bss || response->wcid != w ||
	    response->generation != owner->peer.generation ||
	    __builtin_memcmp(response->mac, owner->peer.addr, MAC_ADDR_LEN) ||
	    __builtin_memcmp(response->bssid,
		ad->ApCfg.MBSSID[owner->peer.bss].wdev.bssid, MAC_ADDR_LEN) ||
	    !wr_ft_iapp_token_finish_locked(&owner->state->ledger, &owner->response))
		return 0;
	if (owner->state->auth_hold[w].active) {
		if (!wr_ft_iapp_auth_hold_release_locked(ad, owner->state, w))
			return 0;
		wr_ft_iapp_token_clear(&owner->state->request_by_wcid[w]);
	}
	owner->active = 0;
	owner->adapter = NULL;
	owner->state = NULL;
	wr_ft_iapp_token_clear(&owner->request);
	wr_ft_iapp_token_clear(&owner->response);
	return 1;
}

/* A failed cache transaction releases response ownership without consuming
 * the AUTH request token; the same request may be retried or timed out. */
static inline int wr_ft_iapp_auth_response_retry_locked(RTMP_ADAPTER *ad,
	struct wr_ft_iapp_auth_response *owner)
{
	unsigned int w;
	struct wr_ft_iapp_token_entry *response;
	if (!ad || !owner || !owner->active || owner->adapter != ad ||
	    owner->state != &ad->wr_ft_iapp_requests)
		return 0;
	w = owner->peer.wcid;
	if (w >= WR_FT_IAPP_TOKEN_CAPACITY || w >= MAX_LEN_OF_MAC_TABLE ||
	    owner->peer.bss >= ad->ApCfg.BssidNum ||
	    !wr_ft_iapp_auth_request_owner_locked(ad, owner->state,
			&owner->request) ||
	    ad->wr_ft_iapp_requests.request_by_wcid[w].serial != owner->request.serial ||
	    ad->wr_ft_iapp_requests.request_by_wcid[w].slot != owner->request.slot ||
	    owner->response.slot >= WR_FT_IAPP_TOKEN_CAPACITY)
		return 0;
	response = &owner->state->ledger.entry[owner->response.slot];
	if (response->state != WR_FT_IAPP_TOKEN_CLAIMED || response->invalidated ||
	    response->serial != owner->response.serial ||
	    response->bss != owner->peer.bss || response->wcid != w ||
	    response->generation != owner->peer.generation ||
	    __builtin_memcmp(response->mac, owner->peer.addr, MAC_ADDR_LEN) ||
	    __builtin_memcmp(response->bssid,
		ad->ApCfg.MBSSID[owner->peer.bss].wdev.bssid, MAC_ADDR_LEN) ||
	    !wr_ft_iapp_token_unclaim_locked(&owner->state->ledger, &owner->response))
		return 0;
	if (owner->state->auth_hold[w].active &&
	    !wr_ft_iapp_auth_hold_detach_locked(ad, owner->state, w))
		return 0;
	owner->active = 0;
	owner->adapter = NULL;
	owner->state = NULL;
	wr_ft_iapp_token_clear(&owner->request);
	wr_ft_iapp_token_clear(&owner->response);
	return 1;
}

#endif
