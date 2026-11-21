#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "ft-iapp-response-token.h"

static void set_token(unsigned char token[WR_FT_IAPP_TOKEN_BYTES],
	unsigned int value)
{
	unsigned int i;
	for (i = 0; i < WR_FT_IAPP_TOKEN_BYTES; i++)
		token[i] = (unsigned char)(value + i + 1U);
}

int main(void)
{
	struct wr_ft_iapp_token_ledger ledger;
	struct wr_ft_iapp_token_handle pending, response, timed_out, raced;
	unsigned char token[WR_FT_IAPP_TOKEN_BYTES];
	unsigned char unpacked[WR_FT_IAPP_TOKEN_BYTES] = { 0 };
	unsigned char element_rsv[3] = { 0 }, keyinfo_rsv[4] = { 0 };
	unsigned char mac[6] = { 2, 3, 4, 5, 6, 7 };
	unsigned char bssid[6] = { 8, 9, 10, 11, 12, 13 };
	unsigned char other_mac[6] = { 2, 3, 4, 5, 6, 8 };
	unsigned char other_bssid[6] = { 8, 9, 10, 11, 12, 14 };
	unsigned int i;

	wr_ft_iapp_token_ledger_init(&ledger);
	set_token(token, 1);
	assert(wr_ft_iapp_token_pack_reserved(element_rsv, keyinfo_rsv, token));
	assert(wr_ft_iapp_token_unpack_reserved(element_rsv, keyinfo_rsv, unpacked));
	assert(wr_ft_iapp_token_equal(token, unpacked));
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &pending));
	assert(!wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 8, 100,
		other_mac, other_bssid, &response));
	assert(!wr_ft_iapp_token_reserve_locked(&ledger, (unsigned char[7]){0},
		2, 7, 99, mac, bssid, &response));
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, other_mac, bssid,
		&response));
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, mac, other_bssid,
		&response));
	assert(wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid,
		&response));
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid,
		&timed_out));
	assert(wr_ft_iapp_token_context_matches_locked(&ledger, &response, 2, 7,
		99, mac, bssid));
	assert(!wr_ft_iapp_token_context_matches_locked(&ledger, &response, 1, 7,
		99, mac, bssid));
	assert(!wr_ft_iapp_token_context_matches_locked(&ledger, &response, 2, 7,
		100, mac, bssid));
	assert(wr_ft_iapp_token_finish_locked(&ledger, &response));
	assert(!wr_ft_iapp_token_finish_locked(&ledger, &response));
	puts("PASS | FT IAPP response token | exact token/MAC/R1KHID, single claim and BSS/WCID/generation context");

	set_token(token, 20);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &timed_out));
	assert(wr_ft_iapp_token_cancel_waiting_locked(&ledger, &timed_out));
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid,
		&response));
	assert(!wr_ft_iapp_token_cancel_waiting_locked(&ledger, &timed_out));
	puts("PASS | FT IAPP timeout race | timeout-first cancellation rejects delayed response; stale handle cannot cancel reused slot");

	set_token(token, 30);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &pending));
	set_token(token, 31);
	assert(wr_ft_iapp_token_replace_waiting_locked(&ledger, 2, 7, 99, mac));
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &timed_out));
	assert(!wr_ft_iapp_token_claim_locked(&ledger, (unsigned char[7]){
		31, 32, 33, 34, 35, 36, 37 }, mac, bssid, &response));
	assert(wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid, &response));
	assert(!wr_ft_iapp_token_replace_waiting_locked(&ledger, 2, 7, 99, mac));
	assert(wr_ft_iapp_token_finish_locked(&ledger, &response));
	puts("PASS | FT IAPP request supersession | newer attempt retires old waiting token; claimed attempt cannot be replaced");

	set_token(token, 40);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &raced));
	assert(wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid,
		&response));
	assert(!wr_ft_iapp_token_cancel_waiting_locked(&ledger, &raced));
	assert(wr_ft_iapp_token_retire_peer_locked(&ledger, 2, 7, 99, mac) == 1);
	assert(!wr_ft_iapp_token_context_matches_locked(&ledger, &response, 2, 7,
		99, mac, bssid));
	assert(wr_ft_iapp_token_finish_locked(&ledger, &response));
	puts("PASS | FT IAPP claim-first retirement | claimed token cannot be timeout-cancelled; association retirement invalidates cache admission");

	wr_ft_iapp_token_ledger_init(&ledger);
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		unsigned char distinct_mac[6] = { 0, 0, 0, 0, (unsigned char)(i >> 8), (unsigned char)i };
		unsigned char distinct_bssid[6] = { 1, 1, 1, 1, 1, (unsigned char)i };
		set_token(token, i + 80U);
		assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 1, i + 1U,
			i + 10U, distinct_mac, distinct_bssid, &pending));
	}
	set_token(token, 200);
	assert(!wr_ft_iapp_token_reserve_locked(&ledger, token, 3, 99, 101,
		mac, bssid, &pending));
	assert(!ledger.poisoned);
	puts("PASS | FT IAPP token ledger bounds | bounded capacity refusal preserves existing pending requests");

	wr_ft_iapp_token_ledger_init(&ledger);
	set_token(token, 210);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &pending));
	assert(wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid, &raced));
	assert(wr_ft_iapp_token_finish_locked(&ledger, &raced));
	set_token(token, 211);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 100,
		mac, bssid, &pending));
	assert(wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid, &response));
	assert(response.slot == raced.slot && response.serial != raced.serial);
	assert(!wr_ft_iapp_token_finish_locked(&ledger, &raced));
	assert(wr_ft_iapp_token_context_matches_locked(&ledger, &response,
		2, 7, 100, mac, bssid));
	assert(wr_ft_iapp_token_finish_locked(&ledger, &response));
	puts("PASS | FT IAPP reused slot | old claimed handle cannot finish a newer generation request");

	wr_ft_iapp_token_ledger_init(&ledger);
	ledger.next_serial = ~0U - 1U;
	set_token(token, 220);
	assert(wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 99,
		mac, bssid, &pending));
	assert(pending.serial == ~0U);
	assert(wr_ft_iapp_token_cancel_waiting_locked(&ledger, &pending));
	set_token(token, 221);
	assert(!wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 100,
		mac, bssid, &pending));
	assert(ledger.poisoned && ledger.next_serial == ~0U);
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid, &response));
	puts("PASS | FT IAPP serial exhaustion | no wrap or request admission after serial exhaustion");

	pending.slot=7;pending.serial=123;
	assert(!wr_ft_iapp_token_reserve_locked(NULL, token, 2, 7, 100,
		mac, bssid, &pending));
	assert(!pending.slot && !pending.serial);
	response.slot=7;response.serial=123;
	assert(!wr_ft_iapp_token_claim_locked(&ledger, token, mac, bssid, &response));
	assert(!response.slot && !response.serial);
	wr_ft_iapp_token_ledger_init(&ledger);
	pending.slot=7;pending.serial=123;
	assert(!wr_ft_iapp_token_reserve_locked(&ledger, token, 2, 7, 0,
		mac, bssid, &pending));
	assert(!pending.slot && !pending.serial);
	response.slot=7;response.serial=123;
	assert(!wr_ft_iapp_token_claim_locked(&ledger, NULL, mac, bssid, &response));
	assert(!response.slot && !response.serial);
	puts("PASS | FT IAPP refused output | invalid input and poisoned ledger clear stale output handles");

	wr_ft_iapp_token_ledger_init(&ledger);
	ledger.next_serial=~0U-1U;
	set_token(token,230);
	assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,99,
		mac,bssid,&pending));
	assert(wr_ft_iapp_token_claim_locked(&ledger,token,mac,bssid,&response));
	set_token(token,231);
	assert(!wr_ft_iapp_token_reserve_locked(&ledger,token,3,8,100,
		other_mac,other_bssid,&pending));
	assert(ledger.poisoned);
	assert(!wr_ft_iapp_token_context_matches_locked(&ledger,&response,
		2,7,99,mac,bssid));
	assert(wr_ft_iapp_token_finish_locked(&ledger,&response));
	assert(!wr_ft_iapp_token_finish_locked(&ledger,&response));
	puts("PASS | FT IAPP poisoned claim | context admission refused while exact claimed cleanup remains single-use");

	wr_ft_iapp_token_ledger_init(&ledger);
	set_token(token,240);
	assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,99,
		mac,bssid,&pending));
	assert(!wr_ft_iapp_token_claim_context_locked(&ledger,token,mac,bssid,
		2,7,100,mac,bssid,&response));
	assert(!response.serial);
	assert(ledger.entry[pending.slot].state==WR_FT_IAPP_TOKEN_FREE);
	assert(!wr_ft_iapp_token_claim_locked(&ledger,token,mac,bssid,&response));
	set_token(token,241);
	assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,100,
		mac,bssid,&pending));
	assert(wr_ft_iapp_token_claim_context_locked(&ledger,token,mac,bssid,
		2,7,100,mac,bssid,&response));
	assert(wr_ft_iapp_token_finish_locked(&ledger,&response));
	puts("PASS | FT IAPP combined admission | stale context retires token without claim leak; exact current context admitted");

	wr_ft_iapp_token_ledger_init(&ledger);set_token(token,250);
	assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,100,mac,bssid,&pending));
	assert(wr_ft_iapp_token_request_end_locked(&ledger,&pending));
	assert(!pending.serial);
	assert(!wr_ft_iapp_token_claim_locked(&ledger,token,mac,bssid,&response));
	set_token(token,251);
	assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,100,mac,bssid,&pending));
	assert(wr_ft_iapp_token_claim_locked(&ledger,token,mac,bssid,&response));
	assert(!wr_ft_iapp_token_request_end_locked(&ledger,&pending));
	assert(pending.serial==response.serial);
	assert(wr_ft_iapp_token_finish_locked(&ledger,&response));
	assert(wr_ft_iapp_token_request_end_locked(&ledger,&pending));
	assert(!pending.serial);
	puts("PASS | FT IAPP AUTH end | waiting request cancelled; claimed response blocks owner exit until response finish");
	return 0;
}
