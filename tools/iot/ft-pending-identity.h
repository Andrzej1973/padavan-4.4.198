/* Bounded identity tickets for first-peer FT requests. Not installed yet.
 * All functions ending in _locked require the caller to own MacTabLock.
 * Retired records remain unavailable until every queued/active reference is
 * released, so an old queue element can never adopt a recycled ledger slot.
 */
#ifndef WR_IOT_FT_PENDING_IDENTITY_H
#define WR_IOT_FT_PENDING_IDENTITY_H

#ifndef WR_FT_PENDING_CAPACITY
#define WR_FT_PENDING_CAPACITY MAX_LEN_OF_MAC_TABLE
#endif

#define WR_FT_PENDING_FREE 0
#define WR_FT_PENDING_LIVE 1
#define WR_FT_PENDING_RETIRED 2
#define WR_FT_PENDING_CLAIMED 3

struct wr_ft_pending_token {
	unsigned int generation;
	unsigned int slot;
	unsigned int bss;
	unsigned char addr[MAC_ADDR_LEN];
};

struct wr_ft_pending_ledger {
	unsigned int next_generation[WR_FT_PENDING_CAPACITY];
	unsigned int generation[WR_FT_PENDING_CAPACITY];
	unsigned int references[WR_FT_PENDING_CAPACITY];
	unsigned int bss[WR_FT_PENDING_CAPACITY];
	unsigned char addr[WR_FT_PENDING_CAPACITY][MAC_ADDR_LEN];
	unsigned char state[WR_FT_PENDING_CAPACITY];
	unsigned char poisoned[WR_FT_PENDING_CAPACITY];
};

static inline void wr_ft_pending_token_clear(struct wr_ft_pending_token *token)
{
	unsigned int i;
	if (!token)
		return;
	token->generation = 0;
	token->slot = 0;
	token->bss = 0;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		token->addr[i] = 0;
}

/* Call exactly once after allocating a fresh adapter, before queue ingress. */
static inline void wr_ft_pending_ledger_init(struct wr_ft_pending_ledger *ledger)
{
	unsigned int i, j;
	if (!ledger)
		return;
	for (i = 0; i < WR_FT_PENDING_CAPACITY; i++) {
		ledger->next_generation[i] = 0;
		ledger->generation[i] = 0;
		ledger->references[i] = 0;
		ledger->bss[i] = 0;
		ledger->state[i] = WR_FT_PENDING_FREE;
		ledger->poisoned[i] = 0;
		for (j = 0; j < MAC_ADDR_LEN; j++)
			ledger->addr[i][j] = 0;
	}
}

static inline int wr_ft_pending_key_equal(const struct wr_ft_pending_ledger *ledger,
	unsigned int slot, unsigned int bss, const unsigned char *addr)
{
	unsigned int i;
	if (!ledger || slot >= WR_FT_PENDING_CAPACITY || !addr ||
		ledger->bss[slot] != bss)
		return 0;
	for (i = 0; i < MAC_ADDR_LEN; i++)
		if (ledger->addr[slot][i] != addr[i])
			return 0;
	return 1;
}

static inline int wr_ft_pending_reserve_locked(struct wr_ft_pending_ledger *ledger,
	unsigned int bss, const unsigned char *addr,
	struct wr_ft_pending_token *token)
{
	unsigned int i, j;
	if (!token)
		return 0;
	wr_ft_pending_token_clear(token);
	if (!ledger || !addr)
		return 0;

	for (i = 0; i < WR_FT_PENDING_CAPACITY; i++) {
		/* Never mint a second insert authority while one is being consumed. */
		if (ledger->state[i] == WR_FT_PENDING_CLAIMED &&
			wr_ft_pending_key_equal(ledger, i, bss, addr))
			return 0;
		if (ledger->state[i] == WR_FT_PENDING_LIVE &&
			wr_ft_pending_key_equal(ledger, i, bss, addr)) {
			if (ledger->references[i] == ~0U)
				return 0;
			ledger->references[i]++;
			token->generation = ledger->generation[i];
			token->slot = i;
			token->bss = bss;
			for (j = 0; j < MAC_ADDR_LEN; j++)
				token->addr[j] = addr[j];
			return token->generation != 0;
		}
	}

	for (i = 0; i < WR_FT_PENDING_CAPACITY; i++) {
		if (ledger->state[i] != WR_FT_PENDING_FREE || ledger->references[i] ||
			ledger->poisoned[i])
			continue;
		if (ledger->next_generation[i] == ~0U) {
			ledger->poisoned[i] = 1;
			continue;
		}
		ledger->next_generation[i]++;
		if (!ledger->next_generation[i]) {
			ledger->poisoned[i] = 1;
			continue;
		}
		ledger->generation[i] = ledger->next_generation[i];
		ledger->references[i] = 1;
		ledger->bss[i] = bss;
		ledger->state[i] = WR_FT_PENDING_LIVE;
		for (j = 0; j < MAC_ADDR_LEN; j++) {
			ledger->addr[i][j] = addr[j];
			token->addr[j] = addr[j];
		}
		token->generation = ledger->generation[i];
		token->slot = i;
		token->bss = bss;
		return 1;
	}
	return 0;
}

static inline int wr_ft_pending_current_locked(
	const struct wr_ft_pending_ledger *ledger,
	const struct wr_ft_pending_token *token)
{
	return ledger && token && token->generation &&
		token->slot < WR_FT_PENDING_CAPACITY &&
		ledger->state[token->slot] == WR_FT_PENDING_LIVE &&
		ledger->generation[token->slot] == token->generation &&
		ledger->references[token->slot] &&
		wr_ft_pending_key_equal(ledger, token->slot, token->bss, token->addr);
}

/* Exactly one queued first-peer event may claim this identity for insertion. */
static inline int wr_ft_pending_claim_locked(
	struct wr_ft_pending_ledger *ledger,
	const struct wr_ft_pending_token *token)
{
	if (!wr_ft_pending_current_locked(ledger, token))
		return 0;
	ledger->state[token->slot] = WR_FT_PENDING_CLAIMED;
	return 1;
}

/* A failed native insert may return the authority to the still-current ticket. */
static inline int wr_ft_pending_unclaim_locked(
	struct wr_ft_pending_ledger *ledger,
	const struct wr_ft_pending_token *token)
{
	if (!ledger || !token || !token->generation ||
		token->slot >= WR_FT_PENDING_CAPACITY ||
		ledger->state[token->slot] != WR_FT_PENDING_CLAIMED ||
		ledger->generation[token->slot] != token->generation ||
		!ledger->references[token->slot] ||
		!wr_ft_pending_key_equal(ledger, token->slot, token->bss, token->addr))
		return 0;
	ledger->state[token->slot] = WR_FT_PENDING_LIVE;
	return 1;
}

/* Insertion/association of this exact BSS+MAC makes unbound tickets stale. */
static inline unsigned int wr_ft_pending_retire_key_locked(
	struct wr_ft_pending_ledger *ledger,
	unsigned int bss, const unsigned char *addr)
{
	unsigned int i, retired = 0;
	if (!ledger || !addr)
		return 0;
	for (i = 0; i < WR_FT_PENDING_CAPACITY; i++) {
		if ((ledger->state[i] != WR_FT_PENDING_LIVE &&
			ledger->state[i] != WR_FT_PENDING_CLAIMED) ||
			!wr_ft_pending_key_equal(ledger, i, bss, addr))
			continue;
		ledger->state[i] = WR_FT_PENDING_RETIRED;
		retired++;
	}
	return retired;
}

/* A stale token cannot decrement references belonging to a reused slot. */
static inline int wr_ft_pending_release_locked(
	struct wr_ft_pending_ledger *ledger,
	const struct wr_ft_pending_token *token)
{
	unsigned int i, j;
	if (!ledger || !token || !token->generation ||
		token->slot >= WR_FT_PENDING_CAPACITY)
		return 0;
	i = token->slot;
	if (ledger->generation[i] != token->generation ||
		!wr_ft_pending_key_equal(ledger, i, token->bss, token->addr) ||
		!ledger->references[i])
		return 0;
	ledger->references[i]--;
	if (!ledger->references[i]) {
		ledger->state[i] = WR_FT_PENDING_FREE;
		ledger->generation[i] = 0;
		ledger->bss[i] = 0;
		for (j = 0; j < MAC_ADDR_LEN; j++)
			ledger->addr[i][j] = 0;
	}
	return 1;
}

#endif /* WR_IOT_FT_PENDING_IDENTITY_H */
