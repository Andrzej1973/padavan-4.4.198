#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 3
#include "ft-pending-identity.h"

int main(void)
{
	struct wr_ft_pending_ledger ledger;
	struct wr_ft_pending_token first, shared, other_bss, third, reused, full;
	unsigned char mac_a[MAC_ADDR_LEN] = {0, 1, 2, 3, 4, 5};
	unsigned char mac_b[MAC_ADDR_LEN] = {0, 1, 2, 3, 4, 6};

	wr_ft_pending_ledger_init(&ledger);
	assert(wr_ft_pending_reserve_locked(&ledger, 1, mac_a, &first));
	assert(wr_ft_pending_current_locked(&ledger, &first));
	assert(wr_ft_pending_reserve_locked(&ledger, 1, mac_a, &shared));
	assert(shared.slot == first.slot && shared.generation == first.generation);
	assert(ledger.references[first.slot] == 2);
	assert(wr_ft_pending_reserve_locked(&ledger, 2, mac_a, &other_bss));
	assert(other_bss.slot != first.slot);
	assert(wr_ft_pending_current_locked(&ledger, &other_bss));
	assert(wr_ft_pending_reserve_locked(&ledger, 3, mac_b, &third));
	assert(wr_ft_pending_claim_locked(&ledger, &first));
	assert(!wr_ft_pending_current_locked(&ledger, &first));
	assert(!wr_ft_pending_reserve_locked(&ledger, 1, mac_a, &full));
	assert(!wr_ft_pending_claim_locked(&ledger, &shared));
	assert(wr_ft_pending_unclaim_locked(&ledger, &first));
	assert(wr_ft_pending_current_locked(&ledger, &shared));
	assert(wr_ft_pending_claim_locked(&ledger, &first));
	assert(wr_ft_pending_retire_key_locked(&ledger, 1, mac_a) == 1);
	assert(!wr_ft_pending_current_locked(&ledger, &first));
	assert(!wr_ft_pending_unclaim_locked(&ledger, &first));
	assert(wr_ft_pending_current_locked(&ledger, &other_bss));
	assert(!wr_ft_pending_reserve_locked(&ledger, 1, mac_b, &full));
	assert(wr_ft_pending_release_locked(&ledger, &first));
	assert(!wr_ft_pending_reserve_locked(&ledger, 1, mac_b, &full));
	assert(wr_ft_pending_release_locked(&ledger, &shared));
	assert(wr_ft_pending_reserve_locked(&ledger, 1, mac_b, &reused));
	assert(reused.slot == first.slot && reused.generation != first.generation);
	assert(!wr_ft_pending_current_locked(&ledger, &first));
	assert(!wr_ft_pending_release_locked(&ledger, &first));
	assert(wr_ft_pending_current_locked(&ledger, &reused));
	assert(wr_ft_pending_release_locked(&ledger, &reused));
	assert(wr_ft_pending_release_locked(&ledger, &other_bss));
	assert(wr_ft_pending_release_locked(&ledger, &third));

	ledger.next_generation[0] = UINT_MAX;
	assert(wr_ft_pending_reserve_locked(&ledger, 1, mac_a, &full));
	assert(ledger.poisoned[0]);
	assert(full.slot != 0);
	assert(wr_ft_pending_release_locked(&ledger, &full));
	puts("PASS | FT pending identity C helper | BSS+MAC keys, single-use claim, unclaim, retirement, stale-token refusal, safe reuse, overflow poison");
	return 0;
}
