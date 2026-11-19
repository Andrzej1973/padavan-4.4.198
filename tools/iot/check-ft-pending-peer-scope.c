#include <assert.h>
#include <stdio.h>
#include <string.h>

#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 8
#define WR_FT_PENDING_CAPACITY MAX_LEN_OF_MAC_TABLE
#define RESERVED_WCID 0
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define IS_ENTRY_NONE(e) (!(e)->used)
#define SST_NOT_AUTH 0
#define SST_AUTH 1
#define SST_ASSOC 2

#include "ft-pending-identity.h"
#include "peer-table-owner.h"
#include "peer-close-executor.h"

typedef struct wifi_dev { unsigned int func_idx; } WIFI_DEV;
typedef struct mac_entry {
	unsigned int wcid, assoc_gen, func_tb_idx;
	unsigned int used, client, Sst;
	unsigned char Addr[MAC_ADDR_LEN];
	WIFI_DEV *wdev;
} MAC_TABLE_ENTRY;

typedef struct adapter {
	struct wr_ft_pending_ledger wr_ft_pending;
	struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
	struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
	unsigned int wr_assoc_event_users[MAX_LEN_OF_MAC_TABLE];
	unsigned int wr_assoc_generations[MAX_LEN_OF_MAC_TABLE];
	unsigned int wr_assoc_visible[MAX_LEN_OF_MAC_TABLE];
	unsigned char wr_assoc_addr[MAX_LEN_OF_MAC_TABLE][MAC_ADDR_LEN];
	struct {
		unsigned int BssidNum;
		struct { WIFI_DEV wdev; } MBSSID[3];
	} ApCfg;
	struct { MAC_TABLE_ENTRY Content[MAX_LEN_OF_MAC_TABLE]; } MacTab;
	unsigned int MacTabLock;
} RTMP_ADAPTER;

#include "assoc-generation.h"
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,
	MAC_TABLE_ENTRY *entry)
{
	unsigned int i, wcid=entry->wcid;
	ad->wr_assoc_visible[wcid]=0;
	for(i=0;i<MAC_ADDR_LEN;i++)ad->wr_assoc_addr[wcid][i]=entry->Addr[i];
	ad->wr_assoc_visible[wcid]=entry->assoc_gen;
}

#include "ft-pending-peer-scope.h"

static void lock(RTMP_ADAPTER *ad) { assert(!ad->MacTabLock); ad->MacTabLock=1; }
static void unlock(RTMP_ADAPTER *ad) { assert(ad->MacTabLock); ad->MacTabLock=0; }

static void init_adapter(RTMP_ADAPTER *ad)
{
	memset(ad, 0, sizeof(*ad));
	wr_ft_pending_ledger_init(&ad->wr_ft_pending);
	wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
	wr_iot_peer_close_executor_init(&ad->wr_iot_peer_close_executor);
	ad->ApCfg.BssidNum=3;
	for (unsigned int i=0;i<3;i++) ad->ApCfg.MBSSID[i].wdev.func_idx=i;
}

static void set_peer(RTMP_ADAPTER *ad, unsigned int wcid,
	unsigned int bss, const unsigned char *addr, unsigned int generation)
{
	MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[wcid];
	entry->wcid=wcid;entry->assoc_gen=generation;entry->func_tb_idx=bss;
	entry->used=1;entry->client=1;entry->wdev=&ad->ApCfg.MBSSID[bss].wdev;
	memcpy(entry->Addr,addr,MAC_ADDR_LEN);
	ad->wr_assoc_generations[wcid]=generation;
	ad->wr_assoc_visible[wcid]=generation;
	memcpy(ad->wr_assoc_addr[wcid],addr,MAC_ADDR_LEN);
}

static void test_success_and_initial_state(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={0,1,2,3,4,5};
	unsigned int old_generation;
	init_adapter(&ad);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(wr_ft_pending_peer_reserve_slot_locked(&ad,5,&ad.ApCfg.MBSSID[2].wdev,
		&ticket,&scope));
	assert(!scope.generation&&ad.wr_assoc_event_users[5]==1);
	set_peer(&ad,5,2,addr,17);
	assert(wr_ft_pending_peer_publish_locked(&ad,&ad.MacTab.Content[5],&ticket,&scope));
	assert(ad.wr_assoc_event_users[5]==1&&ad.wr_iot_peer_table_owner.transactions==1);
	/* The fresh native entry can be unauthenticated when the lease is acquired. */
	assert(ad.MacTab.Content[5].client&&ad.MacTab.Content[5].assoc_gen==17&&
		ad.MacTab.Content[5].Sst==SST_NOT_AUTH);
	old_generation=scope.generation;
	unlock(&ad);
	/* Successful FT auth advances generation while retaining exact lease. */
	lock(&ad);assert(ad.wr_assoc_event_users[5]);
	ad.MacTab.Content[5].Sst=SST_AUTH;
	assert(wr_ft_pending_peer_advance_locked(&ad,&ad.MacTab.Content[5],&scope));
	assert(scope.generation==18&&ad.wr_assoc_generations[5]==18&&
		ad.wr_assoc_visible[5]==18&&ad.wr_assoc_event_users[5]==1);
	assert(!wr_assoc_generation_matches(old_generation,ad.wr_assoc_visible[5],1,1));
	unlock(&ad);
	lock(&ad);assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
	assert(!ad.wr_assoc_event_users[5]&&!ad.wr_iot_peer_table_owner.transactions&&!scope.active);
	assert(ad.MacTabLock);unlock(&ad);
	lock(&ad);assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&ticket));unlock(&ad);
}

static void test_generation_exhaustion_retains_lease(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={9,9,9,9,9,9};
	init_adapter(&ad);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,1,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(wr_ft_pending_peer_reserve_slot_locked(&ad,3,&ad.ApCfg.MBSSID[1].wdev,
		&ticket,&scope));
	set_peer(&ad,3,1,addr,~0U);
	assert(wr_ft_pending_peer_publish_locked(&ad,&ad.MacTab.Content[3],&ticket,&scope));
	assert(!wr_ft_pending_peer_advance_locked(&ad,&ad.MacTab.Content[3],&scope));
	assert(scope.active&&ad.wr_assoc_event_users[3]==1&&
		ad.wr_iot_peer_table_owner.transactions==1&&ad.wr_iot_peer_table_owner.poisoned);
	assert(ad.MacTab.Content[3].assoc_gen==~0U&&ad.wr_assoc_visible[3]==~0U);
	assert(!wr_ft_pending_peer_leave_locked(&ad,&scope));
	assert(scope.active&&ad.wr_assoc_event_users[3]==1&&
		ad.wr_iot_peer_table_owner.transactions==1);
	unlock(&ad);
}

static void test_context_refusal(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={7,7,7,7,7,7};
	init_adapter(&ad);set_peer(&ad,4,0,addr,3);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(!wr_ft_pending_peer_enter_locked(&ad,&ad.MacTab.Content[4],&ticket,&scope));
	assert(!ad.wr_assoc_event_users[4]&&!ad.wr_iot_peer_table_owner.transactions);
	/* A ticket for this BSS cannot lease a same-context slot with another MAC. */
	set_peer(&ad,4,2,addr,4);
	ad.MacTab.Content[4].Addr[0]^=1;
	assert(!wr_ft_pending_peer_enter_locked(&ad,&ad.MacTab.Content[4],&ticket,&scope));
	assert(!ad.wr_assoc_event_users[4]&&!ad.wr_iot_peer_table_owner.transactions);
	ad.MacTab.Content[4].Addr[0]^=1;
	ad.wr_assoc_visible[4]++;
	assert(!wr_ft_pending_peer_enter_locked(&ad,&ad.MacTab.Content[4],&ticket,&scope));
	assert(!ad.wr_assoc_event_users[4]&&!ad.wr_iot_peer_table_owner.transactions);
	ad.wr_assoc_visible[4]--;
	ad.wr_assoc_generations[4]++;
	assert(!wr_ft_pending_peer_enter_locked(&ad,&ad.MacTab.Content[4],&ticket,&scope));
	assert(!ad.wr_assoc_event_users[4]&&!ad.wr_iot_peer_table_owner.transactions);
	ad.wr_assoc_generations[4]--;
	/* A close executor or owner reset prevents acquiring a new callback lease. */
	ad.wr_iot_peer_close_executor.lane=WR_PEER_CLOSE_LEGACY;
	assert(!wr_ft_pending_peer_enter_locked(&ad,&ad.MacTab.Content[4],&ticket,&scope));
	assert(!ad.wr_iot_peer_table_owner.transactions);
	unlock(&ad);
}

static void test_native_auth_failure_exit(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={3,1,4,1,5,9};
	init_adapter(&ad);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,1,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(wr_ft_pending_peer_reserve_slot_locked(&ad,3,&ad.ApCfg.MBSSID[1].wdev,
		&ticket,&scope));
	set_peer(&ad,3,1,addr,12);
	assert(wr_ft_pending_peer_publish_locked(&ad,&ad.MacTab.Content[3],&ticket,&scope));
	/* A failed FT auth leaves the inserted client unauthenticated. */
	assert(ad.MacTab.Content[3].Sst==SST_NOT_AUTH);
	assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
	assert(!ad.wr_assoc_event_users[3]&&!ad.wr_iot_peer_table_owner.transactions);
	unlock(&ad);
	lock(&ad);assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&ticket));unlock(&ad);
}

static void test_identity_drift_retains_ownership(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={8,6,7,5,3,0};
	init_adapter(&ad);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(wr_ft_pending_peer_reserve_slot_locked(&ad,6,&ad.ApCfg.MBSSID[2].wdev,
		&ticket,&scope));
	set_peer(&ad,6,2,addr,9);
	assert(wr_ft_pending_peer_publish_locked(&ad,&ad.MacTab.Content[6],&ticket,&scope));
	ad.MacTab.Content[6].assoc_gen++;
	assert(!wr_ft_pending_peer_leave_locked(&ad,&scope));
	assert(scope.active&&ad.wr_assoc_event_users[6]==1);
	assert(ad.wr_iot_peer_table_owner.transactions==1&&ad.wr_iot_peer_table_owner.poisoned);
	unlock(&ad);
}

static void test_transaction_underflow_retains_event_user(void)
{
	RTMP_ADAPTER ad;struct wr_ft_pending_token ticket={0};
	struct wr_ft_pending_peer_scope scope={0};unsigned char addr[6]={2,7,1,8,2,8};
	init_adapter(&ad);
	lock(&ad);assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,1,addr,&ticket));
	assert(wr_ft_pending_claim_locked(&ad.wr_ft_pending,&ticket));
	assert(wr_ft_pending_peer_reserve_slot_locked(&ad,2,&ad.ApCfg.MBSSID[1].wdev,
		&ticket,&scope));
	set_peer(&ad,2,1,addr,6);
	assert(wr_ft_pending_peer_publish_locked(&ad,&ad.MacTab.Content[2],&ticket,&scope));
	ad.wr_iot_peer_table_owner.transactions=0;
	assert(!wr_ft_pending_peer_leave_locked(&ad,&scope));
	assert(scope.active&&ad.wr_assoc_event_users[2]==1);
	assert(ad.wr_iot_peer_table_owner.poisoned);
	unlock(&ad);
}

int main(void)
{
	test_success_and_initial_state();
	test_generation_exhaustion_retains_lease();
	test_context_refusal();
	test_native_auth_failure_exit();
	test_identity_drift_retains_ownership();
	test_transaction_underflow_retains_event_user();
	puts("PASS | FT pending inserted-peer scope | exact claimed identity, AUTH generation advance invalidates old stamps, lease release/exhaustion, close refusal and drift retention");
	return 0;
}
