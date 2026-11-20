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
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define WRITE_ONCE(a,b) ((a)=(b))
#define smp_wmb() ((void)0)
#include "ft-pending-identity.h"
#include "peer-table-owner.h"
#include "peer-close-executor.h"
struct wifi_dev {unsigned char bssid[6];unsigned int func_idx;};
typedef struct {unsigned int wcid,func_tb_idx,assoc_gen,client,Sst;
 unsigned char Addr[6];struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {
 struct {unsigned int BssidNum;struct {struct wifi_dev wdev;} MBSSID[3];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[8];} MacTab;
 struct wr_ft_pending_ledger wr_ft_pending;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 unsigned int wr_iot_peer_delete_active;
 unsigned int wr_assoc_event_users[8],wr_assoc_generations[8],wr_assoc_visible[8];
 unsigned char wr_assoc_addr[8][6];
} RTMP_ADAPTER;
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 ad->wr_assoc_visible[entry->wcid]=entry->assoc_gen;
 memcpy(ad->wr_assoc_addr[entry->wcid],entry->Addr,6);
}
#include "ft-auth-request-context.h"
#include "ft-iapp-detached-admission.h"
/* Every helper below runs in a single modeled MacTabLock critical section. */
static void setup(RTMP_ADAPTER *ad,struct wr_ft_iapp_request_state *state,
 unsigned int sst,unsigned char *wire)
{
 struct wr_ft_peer_scope existing={0};struct wr_ft_pending_peer_scope pending={0};
 struct wr_ft_auth_request_context context={&existing,&pending};
 struct wr_ft_iapp_token_handle request={0};
 struct wr_ft_peer_stamp stamp={.generation=3,.wcid=7,.bss=2,.addr={42}};
 struct wr_ft_pending_token ticket={0};unsigned char seed[7]={0};
 MAC_TABLE_ENTRY *entry;
 memset(ad,0,sizeof(*ad));wr_ft_iapp_request_state_init(state);
 assert(wr_ft_iapp_request_state_seed(state,seed));ad->ApCfg.BssidNum=3;
 ad->ApCfg.MBSSID[2].wdev.func_idx=2;ad->ApCfg.MBSSID[2].wdev.bssid[0]=2;
 entry=&ad->MacTab.Content[7];
 *entry=(MAC_TABLE_ENTRY){.wcid=7,.func_tb_idx=2,.assoc_gen=3,.client=1,
  .Sst=sst,.Addr={42},.wdev=&ad->ApCfg.MBSSID[2].wdev};
 ad->wr_assoc_generations[7]=3;wr_assoc_publish_slot_locked(ad,entry);
 if(sst==SST_NOT_AUTH){
  assert(wr_ft_pending_reserve_locked(&ad->wr_ft_pending,2,entry->Addr,&ticket));
  assert(wr_ft_pending_claim_locked(&ad->wr_ft_pending,&ticket));
  assert(wr_ft_pending_peer_enter_locked(ad,entry,&ticket,&pending));
  assert(wr_ft_pending_retire_key_locked(&ad->wr_ft_pending,2,entry->Addr));
  assert(wr_ft_pending_release_locked(&ad->wr_ft_pending,&ticket));
 }else assert(wr_ft_peer_enter_locked(ad,&stamp,&existing));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,&context,state,&request,wire));
 assert(wr_ft_auth_request_detach_locked(ad,entry,&context,state,&request));
 if(pending.active)assert(wr_ft_pending_peer_leave_locked(ad,&pending));
 else assert(wr_ft_peer_leave_locked(ad,&existing));
 assert(!request.serial&&!ad->wr_assoc_event_users[7]&&!ad->wr_iot_peer_table_owner.transactions);
}
int main(void)
{
 unsigned int sst,scenario;
 for(sst=0;sst<=2;sst++)for(scenario=0;scenario<=21;scenario++){
  RTMP_ADAPTER ad,before;struct wr_ft_iapp_request_state state,saved;
  struct wr_ft_iapp_detached_scope scope={0},other={0};
  MAC_TABLE_ENTRY *out=NULL,*entry;unsigned char wire[7],mac[6]={42},bssid[6]={2};
  setup(&ad,&state,sst,wire);entry=&ad.MacTab.Content[7];
  switch(scenario){
   case 1:mac[0]++;break;
   case 2:bssid[0]++;break;
   case 3:wire[0]++;break;
   case 4:entry->wdev=&ad.ApCfg.MBSSID[0].wdev;break;
   case 5:entry->func_tb_idx=1;break;
   case 6:entry->assoc_gen++;break;
   case 7:ad.wr_assoc_visible[7]=0;break;
   case 8:ad.wr_assoc_generations[7]++;break;
   case 9:entry->client=0;break;
   case 10:ad.wr_assoc_event_users[7]=1;break;
   case 11:ad.wr_iot_peer_delete_active=1;break;
   case 12:ad.wr_iot_peer_table_owner.closed=1;break;
   case 13:ad.wr_iot_peer_close_executor.running=1;break;
   case 14:state.current[7].serial++;break;
   case 15:state.detached[7]=0;break;
   case 16:entry->Sst=(sst+1)%3;break;
   case 17:ad.wr_assoc_addr[7][0]++;break;
   case 18:entry->wdev->bssid[0]++;break;
   case 19:state.current[7].slot++;break;
   case 20:state.ledger.entry[state.current[7].slot].invalidated=1;break;
  }
  before=ad;saved=state;
  if(scenario&&scenario!=21){
   assert(!wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&scope,&out));
   assert(!out&&!scope.active&&!memcmp(&before,&ad,sizeof(ad))&&!memcmp(&saved,&state,sizeof(state)));
   continue;
  }
  assert(wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&scope,&out));
  assert(out==entry&&scope.active&&ad.wr_assoc_event_users[7]==1);
  assert(ad.wr_iot_peer_table_owner.transactions==1);
  assert(!wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&scope,&out));
  assert(scope.active&&!out);
  assert(!wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&other,&out));
  if(scenario==21){
   entry->assoc_gen++;
   assert(!wr_ft_iapp_detached_finish_locked(&ad,&state,&scope));
   assert(scope.active&&ad.wr_iot_peer_table_owner.poisoned&&ad.wr_assoc_event_users[7]==1);
   assert(ad.wr_iot_peer_table_owner.transactions==1&&state.detached[7]);
   continue;
  }
  assert(wr_ft_iapp_detached_finish_locked(&ad,&state,&scope));
  assert(!scope.active&&!state.current[7].serial&&!state.detached[7]);
  assert(!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
  assert(!wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&other,&out));
 }
 puts("PASS | FT detached response lease | NOT_AUTH/AUTH/ASSOC exact published token; 20 identity/state/owner refusals; one independent lease; replay refused; balanced finish; uncertain identity retains poisoned ownership");
 return 0;
}
