/* Caller serializes every operation with MacTabLock or an equally strong lock. */
#ifndef WR_IOT_FT_IAPP_RESPONSE_TOKEN_H
#define WR_IOT_FT_IAPP_RESPONSE_TOKEN_H

#define WR_FT_IAPP_TOKEN_BYTES 7
#ifdef MAX_LEN_OF_MAC_TABLE
#define WR_FT_IAPP_TOKEN_CAPACITY MAX_LEN_OF_MAC_TABLE
#else
#define WR_FT_IAPP_TOKEN_CAPACITY 32
#endif
#define WR_FT_IAPP_TOKEN_FREE 0U
#define WR_FT_IAPP_TOKEN_WAITING 1U
#define WR_FT_IAPP_TOKEN_CLAIMED 2U

struct wr_ft_iapp_token_entry {
	unsigned int state;
	unsigned int serial;
	unsigned int bss;
	unsigned int wcid;
	unsigned int generation;
	unsigned int invalidated;
	unsigned char token[WR_FT_IAPP_TOKEN_BYTES];
	unsigned char mac[6];
	unsigned char bssid[6];
};

struct wr_ft_iapp_token_ledger {
	unsigned int next_serial;
	unsigned int poisoned;
	struct wr_ft_iapp_token_entry entry[WR_FT_IAPP_TOKEN_CAPACITY];
};

struct wr_ft_iapp_token_handle {
	unsigned int slot;
	unsigned int serial;
};

static inline void wr_ft_iapp_token_clear(struct wr_ft_iapp_token_handle *handle)
{
	if (handle) {
		handle->slot = 0;
		handle->serial = 0;
	}
}

static inline int wr_ft_iapp_token_nonzero(const unsigned char *token)
{
	unsigned int i;
	unsigned char value = 0;
	if (!token)
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_BYTES; i++)
		value |= token[i];
	return value != 0;
}

static inline int wr_ft_iapp_token_equal(const unsigned char *left,
	const unsigned char *right)
{
	unsigned int i;
	unsigned char difference = 0;
	if (!left || !right)
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_BYTES; i++)
		difference |= left[i] ^ right[i];
	return difference == 0;
}

static inline int wr_ft_iapp_token_pack_reserved(unsigned char *element_rsv,
	unsigned char *keyinfo_rsv, const unsigned char *token)
{
	unsigned int i;
	if (!element_rsv || !keyinfo_rsv || !token)
		return 0;
	for (i = 0; i < 3; i++)
		element_rsv[i] = token[i];
	for (i = 0; i < 4; i++)
		keyinfo_rsv[i] = token[i + 3];
	return 1;
}

static inline int wr_ft_iapp_token_unpack_reserved(const unsigned char *element_rsv,
	const unsigned char *keyinfo_rsv, unsigned char *token)
{
	unsigned int i;
	if (!element_rsv || !keyinfo_rsv || !token)
		return 0;
	for (i = 0; i < 3; i++)
		token[i] = element_rsv[i];
	for (i = 0; i < 4; i++)
		token[i + 3] = keyinfo_rsv[i];
	return 1;
}

static inline void wr_ft_iapp_token_ledger_init(
	struct wr_ft_iapp_token_ledger *ledger)
{
	unsigned int i, j;
	if (!ledger)
		return;
	ledger->next_serial = 0;
	ledger->poisoned = 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[i];
		entry->state = WR_FT_IAPP_TOKEN_FREE;
		entry->serial = 0;
		entry->bss = 0;
		entry->wcid = 0;
		entry->generation = 0;
		entry->invalidated = 0;
		for (j = 0; j < WR_FT_IAPP_TOKEN_BYTES; j++)
			entry->token[j] = 0;
		for (j = 0; j < 6; j++) {
			entry->mac[j] = 0;
			entry->bssid[j] = 0;
		}
	}
}

static inline int wr_ft_iapp_token_reserve_locked(
	struct wr_ft_iapp_token_ledger *ledger, const unsigned char *token,
	unsigned int bss, unsigned int wcid, unsigned int generation,
	const unsigned char *mac, const unsigned char *bssid,
	struct wr_ft_iapp_token_handle *handle)
{
	unsigned int i, j, free_slot = WR_FT_IAPP_TOKEN_CAPACITY;
	wr_ft_iapp_token_clear(handle);
	if (!ledger || !handle || ledger->poisoned || !generation ||
		!mac || !bssid || !wr_ft_iapp_token_nonzero(token))
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[i];
		if (entry->state == WR_FT_IAPP_TOKEN_FREE) {
			if (free_slot == WR_FT_IAPP_TOKEN_CAPACITY)
				free_slot = i;
			continue;
		}
		if (wr_ft_iapp_token_equal(entry->token, token) ||
			(entry->bss == bss && entry->wcid == wcid &&
			 entry->generation == generation &&
			 !__builtin_memcmp(entry->mac, mac, 6)))
			return 0;
	}
	if (free_slot == WR_FT_IAPP_TOKEN_CAPACITY)
		return 0;
	if (ledger->next_serial == ~0U) {
		ledger->poisoned = 1;
		return 0;
	}
	{
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[free_slot];
		entry->serial = ++ledger->next_serial;
		entry->state = WR_FT_IAPP_TOKEN_WAITING;
		entry->bss = bss;
		entry->wcid = wcid;
		entry->generation = generation;
		entry->invalidated = 0;
		for (j = 0; j < WR_FT_IAPP_TOKEN_BYTES; j++)
			entry->token[j] = token[j];
		for (j = 0; j < 6; j++) {
			entry->mac[j] = mac[j];
			entry->bssid[j] = bssid[j];
		}
		handle->slot = free_slot;
		handle->serial = entry->serial;
	}
	return 1;
}

static inline int wr_ft_iapp_token_claim_locked(
	struct wr_ft_iapp_token_ledger *ledger, const unsigned char *token,
	const unsigned char *response_mac, const unsigned char *response_r1khid,
	struct wr_ft_iapp_token_handle *handle)
{
	unsigned int i, j;
	wr_ft_iapp_token_clear(handle);
	if (!ledger || !handle || ledger->poisoned || !response_mac ||
		!response_r1khid || !wr_ft_iapp_token_nonzero(token))
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[i];
		unsigned char mac_diff = 0, bssid_diff = 0;
		if (entry->state != WR_FT_IAPP_TOKEN_WAITING ||
			entry->invalidated || !wr_ft_iapp_token_equal(entry->token, token))
			continue;
		for (j = 0; j < 6; j++) {
			mac_diff |= entry->mac[j] ^ response_mac[j];
			bssid_diff |= entry->bssid[j] ^ response_r1khid[j];
		}
		if (mac_diff || bssid_diff)
			return 0;
		entry->state = WR_FT_IAPP_TOKEN_CLAIMED;
		handle->slot = i;
		handle->serial = entry->serial;
		return 1;
	}
	return 0;
}

/* Replace only an older unclaimed attempt for the same live association.
 * A response that already claimed its token owns the race; do not supersede it.
 */
static inline int wr_ft_iapp_token_replace_waiting_locked(
	struct wr_ft_iapp_token_ledger *ledger, unsigned int bss,
	unsigned int wcid, unsigned int generation, const unsigned char *mac)
{
	unsigned int i, j;
	if (!ledger || ledger->poisoned || !generation || !mac)
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[i];
		unsigned char mac_diff = 0;
		if (entry->state == WR_FT_IAPP_TOKEN_FREE || entry->bss != bss ||
			entry->wcid != wcid || entry->generation != generation)
			continue;
		for (j = 0; j < 6; j++)
			mac_diff |= entry->mac[j] ^ mac[j];
		if (mac_diff)
			continue;
		if (entry->state == WR_FT_IAPP_TOKEN_CLAIMED)
			return 0;
		entry->state = WR_FT_IAPP_TOKEN_FREE;
		entry->invalidated = 1;
	}
	return 1;
}

static inline int wr_ft_iapp_token_context_matches_locked(
	const struct wr_ft_iapp_token_ledger *ledger,
	const struct wr_ft_iapp_token_handle *handle, unsigned int bss,
	unsigned int wcid, unsigned int generation, const unsigned char *mac,
	const unsigned char *bssid)
{
	const struct wr_ft_iapp_token_entry *entry;
	unsigned int j;
	unsigned char mac_diff = 0, bssid_diff = 0;
	if (!ledger || !handle || ledger->poisoned || !mac || !bssid ||
		handle->slot >= WR_FT_IAPP_TOKEN_CAPACITY || !handle->serial)
		return 0;
	entry = &ledger->entry[handle->slot];
	if (entry->state != WR_FT_IAPP_TOKEN_CLAIMED ||
		entry->serial != handle->serial || entry->invalidated ||
		entry->bss != bss || entry->wcid != wcid ||
		entry->generation != generation)
		return 0;
	for (j = 0; j < 6; j++) {
		mac_diff |= entry->mac[j] ^ mac[j];
		bssid_diff |= entry->bssid[j] ^ bssid[j];
	}
	return !mac_diff && !bssid_diff;
}

/* Timeout may cancel only if it wins before response claim. */
static inline int wr_ft_iapp_token_cancel_waiting_locked(
	struct wr_ft_iapp_token_ledger *ledger,
	const struct wr_ft_iapp_token_handle *handle)
{
	struct wr_ft_iapp_token_entry *entry;
	if (!ledger || !handle || handle->slot >= WR_FT_IAPP_TOKEN_CAPACITY ||
		!handle->serial)
		return 0;
	entry = &ledger->entry[handle->slot];
	if (entry->state != WR_FT_IAPP_TOKEN_WAITING ||
		entry->serial != handle->serial)
		return 0;
	entry->state = WR_FT_IAPP_TOKEN_FREE;
	entry->invalidated = 1;
	return 1;
}

static inline int wr_ft_iapp_token_retire_peer_locked(
	struct wr_ft_iapp_token_ledger *ledger, unsigned int bss,
	unsigned int wcid, unsigned int generation, const unsigned char *mac)
{
	unsigned int i, j, retired = 0;
	if (!ledger || !mac)
		return 0;
	for (i = 0; i < WR_FT_IAPP_TOKEN_CAPACITY; i++) {
		struct wr_ft_iapp_token_entry *entry = &ledger->entry[i];
		unsigned char mac_diff = 0;
		if (entry->state == WR_FT_IAPP_TOKEN_FREE || entry->bss != bss ||
			entry->wcid != wcid || entry->generation != generation)
			continue;
		for (j = 0; j < 6; j++)
			mac_diff |= entry->mac[j] ^ mac[j];
		if (mac_diff)
			continue;
		if (entry->state == WR_FT_IAPP_TOKEN_WAITING)
			entry->state = WR_FT_IAPP_TOKEN_FREE;
		entry->invalidated = 1;
		retired++;
	}
	return (int)retired;
}

static inline int wr_ft_iapp_token_finish_locked(
	struct wr_ft_iapp_token_ledger *ledger,
	const struct wr_ft_iapp_token_handle *handle)
{
	struct wr_ft_iapp_token_entry *entry;
	if (!ledger || !handle || handle->slot >= WR_FT_IAPP_TOKEN_CAPACITY ||
		!handle->serial)
		return 0;
	entry = &ledger->entry[handle->slot];
	if (entry->state != WR_FT_IAPP_TOKEN_CLAIMED ||
		entry->serial != handle->serial)
		return 0;
	entry->state = WR_FT_IAPP_TOKEN_FREE;
	entry->invalidated = 1;
	return 1;
}

#endif
