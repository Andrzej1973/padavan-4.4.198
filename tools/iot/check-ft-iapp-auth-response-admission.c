#include <assert.h>
#include <stdio.h>
#include <string.h>

#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 8
#define RESERVED_WCID 0
#define SST_NOT_AUTH 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define IS_ENTRY_NONE(e) (!(e)->client)
#define MAC_ADDR_EQUAL(a,b) (!memcmp((a),(b),MAC_ADDR_LEN))
#define WRITE_ONCE(a,b) ((a)=(b))
#define smp_wmb() ((void)0)
#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include "ft-pending-identity.h"
#include "ft-iapp-request-state.h"

struct wifi_dev { unsigned char bssid[6]; unsigned int func_idx; };
typedef struct {
	unsigned int wcid,func_tb_idx,assoc_gen,client,Sst;
	unsigned char Addr[6];
	struct wifi_dev *wdev;
} MAC_TABLE_ENTRY;
struct wr_iot_peer_table_owner;
struct wr_iot_peer_close_executor;
struct wr_ft_iapp_request_state;
typedef struct _RTMP_ADAPTER {
	int MacTabLock;
	struct {
		unsigned int BssidNum;
		struct { struct wifi_dev wdev; } MBSSID[3];
	} ApCfg;
	struct { MAC_TABLE_ENTRY Content[MAX_LEN_OF_MAC_TABLE]; } MacTab;
	struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
	struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
	struct wr_ft_pending_ledger wr_ft_pending;
	unsigned int wr_iot_peer_delete_active;
	unsigned int wr_assoc_event_users[MAX_LEN_OF_MAC_TABLE];
	unsigned int wr_assoc_generations[MAX_LEN_OF_MAC_TABLE];
	unsigned int wr_assoc_visible[MAX_LEN_OF_MAC_TABLE];
	unsigned char wr_assoc_addr[MAX_LEN_OF_MAC_TABLE][MAC_ADDR_LEN];
	struct wr_ft_iapp_request_state wr_ft_iapp_requests;
} RTMP_ADAPTER;

static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry) { (void)ad; (void)entry; }

#include "ft-iapp-auth-response-admission.h"

static void NdisAcquireSpinLock(int *lock)
{
	assert(!*lock);
	*lock = 1;
}

static void NdisReleaseSpinLock(int *lock)
{
	assert(*lock);
	*lock = 0;
}

static const unsigned char k_mac[6] = { 0x02,0x11,0x22,0x33,0x44,0x55 };
static const unsigned char k_bssid[6] = { 0x02,0xaa,0xbb,0xcc,0xdd,0xee };
static const unsigned char k_token[WR_FT_IAPP_TOKEN_BYTES] = { 1,2,3,4,5,6,7 };

struct fixture {
	RTMP_ADAPTER ad;
	struct wr_ft_peer_scope peer;
	struct wr_ft_iapp_token_handle request;
};

static void setup(struct fixture *f)
{
	RTMP_ADAPTER *ad = &f->ad;
	struct wr_ft_peer_stamp stamp = { .generation=5, .wcid=3, .bss=1 };
	MAC_TABLE_ENTRY *entry;
	memset(f, 0, sizeof(*f));
	wr_ft_iapp_request_state_init(&ad->wr_ft_iapp_requests);
	wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
	wr_iot_peer_close_executor_init(&ad->wr_iot_peer_close_executor);
	NdisAcquireSpinLock(&ad->MacTabLock);
	ad->ApCfg.BssidNum = 2;
	memcpy(ad->ApCfg.MBSSID[1].wdev.bssid, k_bssid, MAC_ADDR_LEN);
	entry = &ad->MacTab.Content[3];
	*entry = (MAC_TABLE_ENTRY){ .wcid=3, .func_tb_idx=1, .assoc_gen=5,
		.client=1, .Sst=SST_AUTH, .wdev=&ad->ApCfg.MBSSID[1].wdev };
	memcpy(entry->Addr, k_mac, MAC_ADDR_LEN);
	ad->wr_assoc_generations[3] = 5;
	ad->wr_assoc_visible[3] = 5;
	memcpy(ad->wr_assoc_addr[3], k_mac, MAC_ADDR_LEN);
	memcpy(stamp.addr, k_mac, MAC_ADDR_LEN);
	assert(wr_ft_peer_enter_locked(ad, &stamp, &f->peer));
	assert(wr_ft_iapp_peer_request_begin_locked(ad, &ad->wr_ft_iapp_requests.ledger,
		k_token, &stamp, &f->request));
	ad->wr_ft_iapp_requests.request_by_wcid[3] = f->request;
}

static void setup_pending(struct fixture *f)
{
	RTMP_ADAPTER *ad = &f->ad;
	MAC_TABLE_ENTRY *entry;
	memset(f, 0, sizeof(*f));
	wr_ft_iapp_request_state_init(&ad->wr_ft_iapp_requests);
	wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
	wr_iot_peer_close_executor_init(&ad->wr_iot_peer_close_executor);
	NdisAcquireSpinLock(&ad->MacTabLock);
	ad->ApCfg.BssidNum = 2;
	memcpy(ad->ApCfg.MBSSID[1].wdev.bssid, k_bssid, MAC_ADDR_LEN);
	entry = &ad->MacTab.Content[3];
	*entry = (MAC_TABLE_ENTRY){ .wcid=3, .func_tb_idx=1, .assoc_gen=5,
		.client=1, .Sst=SST_NOT_AUTH, .wdev=&ad->ApCfg.MBSSID[1].wdev };
	memcpy(entry->Addr, k_mac, MAC_ADDR_LEN);
	ad->wr_assoc_generations[3] = 5;
	ad->wr_assoc_visible[3] = 5;
	memcpy(ad->wr_assoc_addr[3], k_mac, MAC_ADDR_LEN);
	assert(wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner));
	ad->wr_assoc_event_users[3] = 1; /* owned by the pending AUTH scope */
	assert(wr_ft_iapp_token_reserve_locked(&ad->wr_ft_iapp_requests.ledger,
		k_token, 1, 3, 5, k_mac, k_bssid, &f->request));
	ad->wr_ft_iapp_requests.request_by_wcid[3] = f->request;
}

static void release_peer(struct fixture *f)
{
	assert(wr_ft_peer_leave_locked(&f->ad, &f->peer));
	assert(!f->ad.wr_assoc_event_users[3]);
	assert(!f->ad.wr_iot_peer_table_owner.transactions);
	NdisReleaseSpinLock(&f->ad.MacTabLock);
}

static void release_pending(struct fixture *f)
{
	assert(f->ad.MacTabLock);
	wr_ft_iapp_token_clear(&f->ad.wr_ft_iapp_requests.request_by_wcid[3]);
	wr_ft_iapp_token_clear(&f->request);
	f->ad.wr_assoc_event_users[3] = 0;
	assert(wr_iot_peer_table_transaction_leave(&f->ad.wr_iot_peer_table_owner));
	assert(!f->ad.wr_assoc_event_users[3]);
	assert(!f->ad.wr_iot_peer_table_owner.transactions);
	NdisReleaseSpinLock(&f->ad.MacTabLock);
}

static void test_first_peer_response(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	setup_pending(&f);
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	assert(owner.active && owner.peer.wcid == 3 && owner.peer.bss == 1);
	assert(f.ad.MacTab.Content[3].Sst == SST_NOT_AUTH);
	assert(f.ad.wr_assoc_event_users[3] == 1);
	assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	assert(!f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
	assert(!owner.active);
	assert(f.ad.wr_ft_iapp_requests.ledger.entry[f.request.slot].state ==
		WR_FT_IAPP_TOKEN_FREE);
	/* Response finish borrows the pending AUTH lease; only AUTH releases it. */
	assert(f.ad.wr_assoc_event_users[3] == 1);
	assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
	release_pending(&f);
}

static void test_response_token_derives_bss(void)
{
	unsigned int scenario;
	for (scenario = 0; scenario < 4; scenario++) {
		struct fixture f;
		struct wr_ft_iapp_auth_response owner = {0};
		unsigned char wrong_mac[MAC_ADDR_LEN];
		struct wr_ft_iapp_token_entry duplicate;
		setup(&f);
		memcpy(wrong_mac, k_mac, sizeof(wrong_mac));
		switch (scenario) {
		case 1:
			wrong_mac[0]++;
			break;
		case 2:
			f.ad.wr_ft_iapp_requests.ledger.entry[f.request.slot].bss =
				f.ad.ApCfg.BssidNum;
			break;
		case 3:
			duplicate = f.ad.wr_ft_iapp_requests.ledger.entry[f.request.slot];
			f.ad.wr_ft_iapp_requests.ledger.entry[4] = duplicate;
			break;
		}
		if (scenario == 0) {
			assert(wr_ft_iapp_auth_response_enter_token_locked(&f.ad,
				&f.ad.wr_ft_iapp_requests, k_token, k_mac, &owner));
			assert(owner.peer.bss == 1 && owner.peer.wcid == 3);
			assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
		} else {
			assert(!wr_ft_iapp_auth_response_enter_token_locked(&f.ad,
				&f.ad.wr_ft_iapp_requests, k_token, wrong_mac, &owner));
			assert(!owner.active);
		}
		if (scenario == 2)
			f.ad.wr_ft_iapp_requests.ledger.entry[f.request.slot].bss = 1;
		if (scenario == 3)
			memset(&f.ad.wr_ft_iapp_requests.ledger.entry[4], 0,
				sizeof(f.ad.wr_ft_iapp_requests.ledger.entry[4]));
		assert(wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
			&f.ad.wr_ft_iapp_requests.ledger, &f.request));
		wr_ft_iapp_token_clear(&f.ad.wr_ft_iapp_requests.request_by_wcid[3]);
		release_peer(&f);
	}
}

static void test_claimed_auth_owner_transfer_finish(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	struct wr_ft_auth_request_context context;
	setup(&f);
	context = (struct wr_ft_auth_request_context){ &f.peer, NULL };
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	assert(wr_ft_iapp_auth_hold_claimed_locked(&f.ad,
		&f.ad.MacTab.Content[3], &context, &f.ad.wr_ft_iapp_requests));
	assert(!f.peer.active && !f.peer.adapter);
	assert(f.ad.wr_ft_iapp_requests.auth_hold[3].active);
	assert(f.ad.wr_assoc_event_users[3] == 1);
	assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_request_owner_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, &f.request));
	assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
	assert(!owner.active && !f.ad.wr_ft_iapp_requests.auth_hold[3].active);
	assert(!f.ad.wr_ft_iapp_requests.request_by_wcid[3].serial);
	assert(!f.ad.wr_assoc_event_users[3]);
	assert(!f.ad.wr_iot_peer_table_owner.transactions);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
}

static void test_claimed_pending_owner_transfer_retry(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	struct wr_ft_pending_peer_scope pending = {0};
	struct wr_ft_auth_request_context context;
	unsigned int slot;
	setup_pending(&f);
	slot = f.request.slot;
	pending.adapter = &f.ad; pending.wcid = 3; pending.generation = 5;
	pending.bss = 1; pending.active = 1;
	memcpy(pending.addr, k_mac, MAC_ADDR_LEN);
	context = (struct wr_ft_auth_request_context){ NULL, &pending };
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	assert(wr_ft_iapp_auth_hold_claimed_locked(&f.ad,
		&f.ad.MacTab.Content[3], &context, &f.ad.wr_ft_iapp_requests));
	assert(!pending.active && f.ad.wr_assoc_event_users[3] == 1);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_response_retry_locked(&f.ad, &owner));
	assert(!owner.active && !f.ad.wr_ft_iapp_requests.auth_hold[3].active);
	assert(f.ad.wr_ft_iapp_requests.ledger.entry[slot].state ==
		WR_FT_IAPP_TOKEN_WAITING);
	assert(f.ad.wr_ft_iapp_requests.detached[3]);
	assert(f.ad.wr_ft_iapp_requests.detached_sst[3] == SST_NOT_AUTH);
	assert(f.ad.wr_ft_iapp_requests.preauth[3].serial == f.request.serial);
	assert(f.ad.wr_ft_iapp_requests.preauth[3].generation == 5);
	assert(f.ad.wr_ft_iapp_requests.preauth[3].bss == 1);
	assert(!memcmp(f.ad.wr_ft_iapp_requests.preauth[3].mac, k_mac, MAC_ADDR_LEN));
	assert(!f.ad.wr_assoc_event_users[3]);
	assert(!f.ad.wr_iot_peer_table_owner.transactions);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
}

static void test_first_peer_cache_failure_then_retry(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	unsigned int slot;
	setup_pending(&f);
	slot = f.request.slot;
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_response_retry_locked(&f.ad, &owner));
	assert(!owner.active);
	assert(f.ad.wr_ft_iapp_requests.ledger.entry[slot].state ==
		WR_FT_IAPP_TOKEN_WAITING);
	assert(f.ad.wr_assoc_event_users[3] == 1);
	assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
	assert(f.ad.wr_assoc_event_users[3] == 1);
	release_pending(&f);
}

static void test_response_first_and_ack_order(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	unsigned int claimed_slot;
	unsigned int cache_updates = 0, retry_updates = 0, ack_completions = 0;
	setup(&f);
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad, &f.ad.wr_ft_iapp_requests,
		k_token, k_mac, k_bssid, &owner));
	claimed_slot = owner.response.slot;
	assert(f.ad.wr_assoc_event_users[3] == 1);
	assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	/* The cache API owns its separate lifetime lease; it must not nest the
	 * station-table lock with the native R1KH cache lock. */
	assert(!f.ad.MacTabLock);
	cache_updates++;
	/* Concurrent AUTH timeout cannot retire the claimed token or peer lease. */
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(!wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	assert(f.request.serial && owner.active);
	/* Reacquire and resolve by the saved value identity; no entry pointer crossed
	 * the unlocked native cache operation. */
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_peer_owned_locked(&f.ad, &owner.peer));
	assert(&f.ad.MacTab.Content[owner.peer.wcid] == &f.ad.MacTab.Content[3]);
	retry_updates++; ack_completions++;
	assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
	assert(!owner.active && !f.ad.wr_ft_iapp_requests.ledger.entry[claimed_slot].state);
	assert(wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	wr_ft_iapp_token_clear(&f.ad.wr_ft_iapp_requests.request_by_wcid[3]);
	assert(cache_updates == 1 && retry_updates == 1 && ack_completions == 1);
	release_peer(&f);
}

static void test_timeout_first(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	setup(&f);
	assert(wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	wr_ft_iapp_token_clear(&f.ad.wr_ft_iapp_requests.request_by_wcid[3]);
	assert(!wr_ft_iapp_auth_response_enter_locked(&f.ad, &f.ad.wr_ft_iapp_requests,
		k_token, k_mac, k_bssid, &owner));
	assert(!owner.active && f.ad.wr_assoc_event_users[3] == 1);
	release_peer(&f);
}

static void test_refusals(void)
{
	unsigned int scenario;
	for (scenario = 0; scenario < 8; scenario++) {
		struct fixture f;
		struct wr_ft_iapp_auth_response owner = {0};
		MAC_TABLE_ENTRY original_entry;
		struct wr_ft_iapp_token_handle original_current;
		unsigned char token[WR_FT_IAPP_TOKEN_BYTES];
		unsigned char mac[MAC_ADDR_LEN], bssid[MAC_ADDR_LEN];
		setup(&f);
		original_entry = f.ad.MacTab.Content[3];
		original_current = f.ad.wr_ft_iapp_requests.request_by_wcid[3];
		memcpy(token, k_token, sizeof(token));
		memcpy(mac, k_mac, sizeof(mac));
		memcpy(bssid, k_bssid, sizeof(bssid));
		switch (scenario) {
		case 0: token[0]++; break;
		case 1: mac[0]++; break;
		case 2: bssid[0]++; break;
		case 3: f.ad.wr_ft_iapp_requests.detached[3] = 1; break;
		case 4: f.ad.MacTab.Content[3].assoc_gen++; break;
		case 5: f.ad.MacTab.Content[3].func_tb_idx = 0; break;
		case 6: f.ad.wr_ft_iapp_requests.request_by_wcid[3].serial++; break;
		case 7: f.ad.MacTab.Content[3].Sst = 3; break;
		}
		assert(!wr_ft_iapp_auth_response_enter_locked(&f.ad,
			&f.ad.wr_ft_iapp_requests, token, mac, bssid, &owner));
		assert(!owner.active);
		assert(f.ad.wr_assoc_event_users[3] == 1);
		assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
		f.ad.MacTab.Content[3] = original_entry;
		f.ad.wr_ft_iapp_requests.request_by_wcid[3] = original_current;
		f.ad.wr_ft_iapp_requests.detached[3] = 0;
		release_peer(&f);
	}
}

static void test_finish_identity_refusal(void)
{
	unsigned int scenario;
	for (scenario = 0; scenario < 2; scenario++) {
		struct fixture f;
		struct wr_ft_iapp_auth_response owner = {0};
		struct wr_ft_iapp_token_entry *response;
		setup(&f);
		assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
			&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
		NdisReleaseSpinLock(&f.ad.MacTabLock);
		NdisAcquireSpinLock(&f.ad.MacTabLock);
		response = &f.ad.wr_ft_iapp_requests.ledger.entry[owner.response.slot];
		if (scenario == 0) response->mac[0]++;
		else response->bssid[0]++;
		assert(!wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
		assert(owner.active && response->state == WR_FT_IAPP_TOKEN_CLAIMED);
		assert(f.ad.wr_assoc_event_users[3] == 1);
		assert(f.ad.wr_iot_peer_table_owner.transactions == 1);
		NdisReleaseSpinLock(&f.ad.MacTabLock);
	}
}

static void test_cache_failure_does_not_ack(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	unsigned int cache_updates = 0, retry_updates = 0, ack_completions = 0;
	unsigned int claimed_slot, cache_success = 0;
	setup(&f);
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad, &f.ad.wr_ft_iapp_requests,
		k_token, k_mac, k_bssid, &owner));
	claimed_slot = owner.response.slot;
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	/* Model allocation/cache failure outside MacTabLock. */
	assert(!f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_peer_owned_locked(&f.ad, &owner.peer));
	if (cache_success) { cache_updates++; retry_updates++; ack_completions++; }
	assert(wr_ft_iapp_auth_response_retry_locked(&f.ad, &owner));
	assert(!owner.active);
	assert(f.ad.wr_ft_iapp_requests.ledger.entry[claimed_slot].state ==
		WR_FT_IAPP_TOKEN_WAITING);
	assert(!retry_updates && !ack_completions);
	/* A later response for this same AUTH request can claim and complete. */
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	assert(!f.ad.MacTabLock);
	cache_success = 1;
	cache_updates++;
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_peer_owned_locked(&f.ad, &owner.peer));
	retry_updates++; ack_completions++;
	assert(wr_ft_iapp_auth_response_finish_locked(&f.ad, &owner));
	assert(!f.ad.wr_ft_iapp_requests.ledger.entry[claimed_slot].state);
	assert(cache_updates == 1 && retry_updates == 1 && ack_completions == 1);
	assert(wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	wr_ft_iapp_token_clear(&f.ad.wr_ft_iapp_requests.request_by_wcid[3]);
	release_peer(&f);
}

static void test_cache_failure_then_timeout(void)
{
	struct fixture f;
	struct wr_ft_iapp_auth_response owner = {0};
	setup(&f);
	assert(wr_ft_iapp_auth_response_enter_locked(&f.ad,
		&f.ad.wr_ft_iapp_requests, k_token, k_mac, k_bssid, &owner));
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	/* Timeout racing an active response cannot release its peer owner. */
	assert(!wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	assert(owner.active && f.request.serial);
	NdisReleaseSpinLock(&f.ad.MacTabLock);
	NdisAcquireSpinLock(&f.ad.MacTabLock);
	assert(wr_ft_iapp_auth_response_retry_locked(&f.ad, &owner));
	assert(wr_ft_iapp_peer_request_end_locked(&f.ad, &f.peer,
		&f.ad.wr_ft_iapp_requests.ledger, &f.request));
	wr_ft_iapp_token_clear(&f.ad.wr_ft_iapp_requests.request_by_wcid[3]);
	release_peer(&f);
}

int main(void)
{
	test_first_peer_response();
	test_response_token_derives_bss();
	test_claimed_auth_owner_transfer_finish();
	test_claimed_pending_owner_transfer_retry();
	test_first_peer_cache_failure_then_retry();
	test_response_first_and_ack_order();
	test_timeout_first();
	test_refusals();
	test_finish_identity_refusal();
	test_cache_failure_does_not_ack();
	test_cache_failure_then_timeout();
	puts("PASS | active/pending AUTH response lease | exact BSS/MAC/WCID/generation; claimed lease transfers once; finish releases; retry detaches pending identity");
	puts("PASS | native response BSS derivation | exact unique token+MAC selects ledger BSS; wrong MAC, invalid BSS and duplicate token refuse");
	puts("PASS | timeout and response arbitration | timeout-first cancels request; late response refused; 8 stale, detached, token, BSS/MAC and state cases refused");
	puts("PASS | response finish identity | tampered MAC/BSSID retains claimed response and AUTH lease");
	puts("PASS | cache failure response | unclaims for retry without ACK; retry may complete; timeout may cancel and release AUTH lease");
	return 0;
}
