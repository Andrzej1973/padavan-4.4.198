/* Native helper boundary test; not native FT crypto/queue/device execution. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 8
#define RESERVED_WCID 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define WRITE_ONCE(location,value) ((location)=(value))
#define smp_wmb() ((void)0)
#include "peer-table-owner.h"
struct wifi_dev {int id;};
typedef struct {unsigned int assoc_gen,wcid,func_tb_idx;int client,Sst;
 unsigned char Addr[6];struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {struct {unsigned int BssidNum;struct {struct wifi_dev wdev;} MBSSID[3];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[8];} MacTab;
 unsigned int wr_iot_peer_delete_active,wr_assoc_event_users[8];
 unsigned int wr_assoc_generations[8],wr_assoc_visible[8];unsigned char wr_assoc_addr[8][6];
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;} RTMP_ADAPTER;
#include "ft-peer-generation.h"
int main(void){
 RTMP_ADAPTER ad={0},foreign={0};ad.ApCfg.BssidNum=3;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[7];
 *e=(MAC_TABLE_ENTRY){.assoc_gen=1,.wcid=7,.func_tb_idx=2,.client=1,
  .Sst=SST_ASSOC,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 ad.wr_assoc_generations[7]=1;ad.wr_assoc_visible[7]=1;memcpy(ad.wr_assoc_addr[7],e->Addr,6);
 struct wr_ft_peer_stamp stamp={0};struct wr_ft_peer_scope scope={0},other={0};
 assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&stamp));
 assert(wr_ft_peer_current_locked(&ad,&stamp));
 /* A queued value never adopts a later generation from the same slot/MAC. */
 e->assoc_gen=2;ad.wr_assoc_generations[7]=2;ad.wr_assoc_visible[7]=2;
 memcpy(ad.wr_assoc_addr[7],e->Addr,6);assert(!wr_ft_peer_current_locked(&ad,&stamp));
 assert(!wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&stamp));
 assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 assert(ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1);
 assert(!wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner));
 assert(!wr_ft_peer_enter_locked(&ad,&stamp,&other));
 assert(!wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 assert(!wr_ft_peer_leave_locked(&foreign,&scope)&&scope.active);
 assert(wr_ft_peer_leave_locked(&ad,&scope));
 assert(!scope.active&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
 assert(!wr_ft_peer_leave_locked(&ad,&scope));
 /* Successful FT auth advances under the lease and invalidates older stamps. */
 e->Sst=SST_AUTH;assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 assert(wr_ft_peer_advance_locked(&ad,e,&scope));
 assert(scope.stamp.generation==3&&e->assoc_gen==3&&
  ad.wr_assoc_generations[7]==3&&ad.wr_assoc_visible[7]==3&&
  !wr_ft_peer_current_locked(&ad,&stamp));
 stamp=scope.stamp;
 assert(wr_ft_peer_leave_locked(&ad,&scope));
 for(int fault=0;fault<7;fault++){
  MAC_TABLE_ENTRY saved=*e;
  if(fault==0)e->client=0;if(fault==1)e->Sst=0;
  if(fault==2)e->func_tb_idx=0;if(fault==3)e->wdev=&ad.ApCfg.MBSSID[0].wdev;
  if(fault==4)e->wcid=3;if(fault==5)e->Addr[0]=43;if(fault==6)e->assoc_gen=0;
  assert(!wr_ft_peer_current_locked(&ad,&stamp));
  assert(!wr_ft_peer_enter_locked(&ad,&stamp,&scope));*e=saved;
 }
 e->Sst=SST_AUTH;assert(wr_ft_peer_current_locked(&ad,&stamp));
 ad.wr_iot_peer_delete_active=1;assert(!wr_ft_peer_enter_locked(&ad,&stamp,&scope));ad.wr_iot_peer_delete_active=0;
 ad.wr_iot_peer_table_owner.closed=1;assert(!wr_ft_peer_enter_locked(&ad,&stamp,&scope));ad.wr_iot_peer_table_owner.closed=0;
 assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 e->assoc_gen++;assert(!wr_ft_peer_leave_locked(&ad,&scope));
 assert(scope.active&&ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1&&ad.wr_iot_peer_table_owner.poisoned);
 /* Invalid captures initialize output; no stale successful stamp survives. */
 assert(!wr_ft_peer_capture_locked(&ad,8,2,e->Addr,&stamp)&&!stamp.generation);
 assert(!wr_ft_peer_capture_locked(&ad,0,2,e->Addr,&stamp)&&!stamp.generation);
 assert(!wr_ft_peer_capture_locked(&ad,7,3,e->Addr,&stamp)&&!stamp.generation);
	/* Exhaustion retains peer/reset exclusion instead of publishing generation 0. */
	RTMP_ADAPTER exhausted={0};struct wr_ft_peer_scope exhausted_scope={0};
	exhausted.ApCfg.BssidNum=3;MAC_TABLE_ENTRY *last=&exhausted.MacTab.Content[7];
	*last=(MAC_TABLE_ENTRY){.assoc_gen=~0U,.wcid=7,.func_tb_idx=2,.client=1,
	 .Sst=SST_AUTH,.Addr={9},.wdev=&exhausted.ApCfg.MBSSID[2].wdev};
	exhausted.wr_assoc_generations[7]=~0U;exhausted.wr_assoc_visible[7]=~0U;
	memcpy(exhausted.wr_assoc_addr[7],last->Addr,6);
	struct wr_ft_peer_stamp last_stamp={.generation=~0U,.wcid=7,.bss=2,.addr={9}};
	assert(wr_ft_peer_enter_locked(&exhausted,&last_stamp,&exhausted_scope));
	assert(!wr_ft_peer_advance_locked(&exhausted,last,&exhausted_scope));
	assert(exhausted_scope.active&&exhausted.wr_assoc_event_users[7]==1&&
	 exhausted.wr_iot_peer_table_owner.transactions==1&&
	 exhausted.wr_iot_peer_table_owner.poisoned&&last->assoc_gen==~0U);
	assert(!wr_ft_peer_leave_locked(&exhausted,&exhausted_scope));
	assert(exhausted_scope.active&&exhausted.wr_assoc_event_users[7]==1&&
	 exhausted.wr_iot_peer_table_owner.transactions==1);
 puts("PASS | FT active-peer lease | successful AUTH advances generation, stale stamp refused, lease released; exhaustion retains poisoned ownership");
 return 0;
}
