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
 int MacTabLock;
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
#include "ft-preauth-retry.h"
typedef struct {
 unsigned int ft_preauth_serial,ft_preauth_generation,ft_preauth_wcid,ft_preauth_bss;
 unsigned char ft_preauth_mac[6],ft_preauth_bssid[6];
 unsigned int Machine,MsgType,MsgLen,Wcid,assoc_gen,assoc_wcid;
 unsigned char assoc_addr[6],Msg[1600];
 unsigned int ft_pending_generation,ft_pending_slot,ft_pending_bss;
 unsigned char ft_pending_addr[6];
} MLME_QUEUE_ELEM;
#include "ft-preauth-queue.h"
#define AP_AUTH_STATE_MACHINE 8
#define APMT2_PEER_AUTH_REQ 9
#define LENGTH_802_11 24
#define FC_TYPE_MGMT 0
#define SUBTYPE_AUTH 11
static void NdisAcquireSpinLock(int *lock){assert(!*lock);*lock=1;}
static void NdisReleaseSpinLock(int *lock){assert(*lock);*lock=0;}
typedef struct {struct {struct {unsigned char Type,SubType;} FC;
 unsigned char duration[2],Addr1[6],Addr2[6],rest[8];} Hdr;} FRAME_802_11;
#include "ft-auth-retry-peer-scope.h"
#include "ft-iapp-slot-retirement.h"
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
  {
   struct wr_ft_preauth_identity captured={0};
   assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,entry->Addr,&captured)==(sst==SST_NOT_AUTH));
   if(sst==SST_NOT_AUTH){
    assert(captured.generation==3&&captured.serial);
    assert(!wr_ft_preauth_retry_capture_locked(&ad,&state,7,1,entry->Addr,&captured));
    assert(!captured.serial);
    entry->assoc_gen++;
    assert(!wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,entry->Addr,&captured));
    entry->assoc_gen--;
    assert(!wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,entry->Addr,&state.preauth[7]));
   }
  }
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
  {
   struct wr_ft_preauth_identity captured={0};
   assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,entry->Addr,&captured)==(sst==SST_NOT_AUTH));
   if(sst==SST_NOT_AUTH){
    state.preauth[7].serial=0;
    assert(!wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,entry->Addr,&captured));
    assert(!captured.serial);
   }
  }
  assert(!wr_ft_iapp_detached_enter_locked(&ad,&state,wire,mac,bssid,&other,&out));
 }
 puts("PASS | FT detached response lease | NOT_AUTH/AUTH/ASSOC exact published token; 20 identity/state/owner refusals; one independent lease; replay refused; balanced finish; uncertain identity retains poisoned ownership");
 puts("PASS | FT preauth retry provenance | pending-origin identity only; exact BSS/MAC/WCID/generation; retained after response finish; generic inactive, wrong BSS, stale generation and output alias refused");
 for(scenario=0;scenario<8;scenario++){
  RTMP_ADAPTER ad;struct wr_ft_iapp_request_state state;
  struct wr_ft_preauth_identity stamp={0};
  struct wr_ft_pending_peer_scope scope={0};MAC_TABLE_ENTRY *entry=NULL;
  unsigned char wire[7];
  setup(&ad,&state,SST_NOT_AUTH,wire);
  assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,ad.MacTab.Content[7].Addr,&stamp));
  {
   MLME_QUEUE_ELEM event={0},saved;
   struct wr_ft_preauth_identity snapshot={0};
   assert(wr_ft_preauth_elem_publish(&event,&stamp));saved=event;
   assert(!wr_ft_preauth_elem_publish(&event,&stamp));
   assert(!memcmp(&event,&saved,sizeof(event)));
   assert(wr_ft_preauth_elem_snapshot(&event,&snapshot));
   assert(snapshot.serial==stamp.serial&&snapshot.generation==stamp.generation);
   assert(!memcmp(snapshot.mac,stamp.mac,6)&&!memcmp(snapshot.bssid,stamp.bssid,6));
   wr_ft_preauth_elem_clear(&event);
   assert(!wr_ft_preauth_elem_snapshot(&event,&snapshot)&&!snapshot.serial);
   assert(wr_ft_preauth_elem_publish(&event,&stamp));
   assert(wr_ft_preauth_elem_snapshot(&event,&stamp));
  }
  switch(scenario){
   case 1:stamp.serial++;break;
   case 2:stamp.generation++;break;
   case 3:stamp.bssid[0]++;break;
   case 4:stamp.mac[0]++;break;
   case 5:stamp.bss=0;break;
   case 6:state.preauth[7].serial++;break;
   case 7:ad.MacTab.Content[7].assoc_gen++;break;
  }
  if(scenario){
   assert(!wr_ft_preauth_retry_enter_locked(&ad,&state,&stamp,&scope,&entry));
   assert(!entry&&!scope.active&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
  }else{
   assert(wr_ft_preauth_retry_enter_locked(&ad,&state,&stamp,&scope,&entry));
   assert(entry==&ad.MacTab.Content[7]&&scope.generation==stamp.generation);
   assert(wr_ft_iapp_pending_owned_locked(&ad,&scope));
   assert(!wr_ft_preauth_retry_enter_locked(&ad,&state,&stamp,&scope,&entry));
   assert(scope.active&&!entry);
   assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
   assert(!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
  }
 }
 puts("PASS | FT preauth retry lease | captured serial/generation/MAC/BSSID/BSS revalidated; changed publication refused; pending AUTH context adopted once and balanced leave");
 puts("PASS | FT preauth queue sidecar | exact serial and identity transfer; occupied metadata preserved; snapshot read-only; cleared reuse refuses stale identity; transferred stamp revalidated before lease");
 for(scenario=0;scenario<15;scenario++){
  RTMP_ADAPTER ad;struct wr_ft_iapp_request_state state;
  struct wr_ft_preauth_identity stamp={0};MLME_QUEUE_ELEM event={0};
  struct wr_ft_pending_peer_scope scope={0};MAC_TABLE_ENTRY *entry=NULL;
  unsigned char wire[7],mac[6]={42};FRAME_802_11 *frame=(FRAME_802_11 *)event.Msg;
  setup(&ad,&state,SST_NOT_AUTH,wire);
  assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,mac,&stamp));
  assert(wr_ft_preauth_elem_publish(&event,&stamp));
  event.Machine=AP_AUTH_STATE_MACHINE;event.MsgType=APMT2_PEER_AUTH_REQ;
  event.MsgLen=30;event.Wcid=event.assoc_wcid=7;event.assoc_gen=3;event.assoc_addr[0]=42;
  frame->Hdr.FC.SubType=SUBTYPE_AUTH;frame->Hdr.Addr1[0]=2;frame->Hdr.Addr2[0]=42;
  event.Msg[24]=2;event.Msg[26]=1;
  switch(scenario){
   case 1:event.ft_pending_generation=1;break;
   case 2:event.assoc_gen++;break;
   case 3:event.assoc_wcid=1;break;
   case 4:event.Wcid=1;break;
   case 5:event.assoc_addr[0]++;break;
   case 6:event.ft_preauth_serial++;break;
   case 7:event.ft_preauth_bssid[0]++;break;
   case 8:event.MsgLen=29;break;
   case 9:event.MsgLen=1601;break;
   case 10:event.Msg[26]=2;break;
   case 11:frame->Hdr.Addr1[0]++;break;
   case 12:frame->Hdr.Addr2[0]++;break;
   case 13:ad.wr_assoc_generations[7]++;break;
   case 14:ad.MacTab.Content[7].Sst=SST_AUTH;break;
  }
  if(scenario){
   assert(!wr_ft_auth_retry_enter_locked(&ad,&state,&event,2,mac,&scope,&entry));
   assert(!entry&&!scope.active&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
  }else{
   assert(wr_ft_auth_retry_enter_locked(&ad,&state,&event,2,mac,&scope,&entry));
   assert(entry==&ad.MacTab.Content[7]&&wr_ft_iapp_pending_owned_locked(&ad,&scope));
   assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
  }
 }
 puts("PASS | FT AUTH retry callback | frame plus queued association and retry provenance match before lease; mixed pending metadata, stale serial/generation, wrong frame/interface and bounds refused");
 {
 RTMP_ADAPTER ad;struct wr_ft_iapp_request_state state;
 struct wr_ft_preauth_identity stamp={0};struct wr_ft_pending_peer_scope scope={0};
 struct wr_ft_auth_request_context context={NULL,&scope};MAC_TABLE_ENTRY *entry=NULL;
 struct wr_ft_iapp_token_handle claim={0};unsigned char wire[7];
 setup(&ad,&state,SST_NOT_AUTH,wire);
 assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,ad.MacTab.Content[7].Addr,&stamp));
 assert(wr_ft_preauth_retry_enter_locked(&ad,&state,&stamp,&scope,&entry));
 assert(wr_ft_iapp_token_claim_locked(&state.ledger,wire,entry->Addr,entry->wdev->bssid,&claim));
 assert(!wr_ft_auth_request_success_prepare_locked(&ad,entry,&context,&state));
 assert(state.preauth[7].serial&&state.current[7].serial&&scope.active);
 assert(wr_ft_iapp_token_finish_locked(&state.ledger,&claim));
 /* A finished record still needs its response cleanup; do not clear it as WAITING. */
 assert(!wr_ft_auth_request_success_prepare_locked(&ad,entry,&context,&state));
 wr_ft_iapp_token_clear(&state.current[7]);state.detached[7]=state.detached_sst[7]=0;
 assert(wr_ft_auth_request_success_prepare_locked(&ad,entry,&context,&state));
 assert(!state.preauth[7].serial&&scope.active);
 assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
 setup(&ad,&state,SST_NOT_AUTH,wire);scope=(struct wr_ft_pending_peer_scope){0};
 assert(wr_ft_preauth_retry_capture_locked(&ad,&state,7,2,ad.MacTab.Content[7].Addr,&stamp));
 assert(wr_ft_preauth_retry_enter_locked(&ad,&state,&stamp,&scope,&entry));
 assert(wr_ft_auth_request_success_prepare_locked(&ad,entry,&context,&state));
 assert(!state.current[7].serial&&!state.detached[7]&&!state.preauth[7].serial);
 assert(!wr_ft_iapp_token_claim_locked(&state.ledger,wire,entry->Addr,entry->wdev->bssid,&claim));
 assert(wr_ft_pending_peer_leave_locked(&ad,&scope));
 }
 puts("PASS | FT AUTH success retirement | WAITING predecessor cancelled before state transition; preauth provenance cleared; claimed/unfinished response blocks success; current lease retained");
 for(scenario=0;scenario<5;scenario++){
  RTMP_ADAPTER ad;struct wr_ft_iapp_request_state state,saved;
  struct wr_ft_iapp_token_handle other={0},claim={0};unsigned char wire[7],foreign[7]={9},mac[6]={66},bssid[6]={2};
  setup(&ad,&state,SST_NOT_AUTH,wire);
  assert(wr_ft_iapp_token_reserve_locked(&state.ledger,foreign,2,6,1,mac,bssid,&other));
  if(scenario==1)ad.wr_assoc_event_users[7]=1;
  if(scenario==2)assert(wr_ft_iapp_token_claim_locked(&state.ledger,wire,ad.MacTab.Content[7].Addr,bssid,&claim));
  if(scenario==3)state.current[7].serial++;
  if(scenario==4)state.current[7].slot=other.slot;
  saved=state;
  if(scenario){assert(!wr_ft_iapp_slot_retire_locked(&ad,&state,7));assert(!memcmp(&state,&saved,sizeof(state)));}
  else{
   unsigned serial=state.ledger.next_serial;
   assert(wr_ft_iapp_slot_retire_locked(&ad,&state,7));
   assert(!state.current[7].serial&&!state.detached[7]&&!state.preauth[7].serial);
   assert(state.ledger.next_serial==serial);
   assert(!memcmp(&state.ledger.entry[other.slot],&saved.ledger.entry[other.slot],sizeof(state.ledger.entry[0])));
   assert(!wr_ft_iapp_token_claim_locked(&state.ledger,wire,ad.MacTab.Content[7].Addr,bssid,&claim));
  }
 }
 puts("PASS | FT slot retirement | WAITING token and preauth invalidated; serial and foreign slot retained; busy, CLAIMED, stale serial and foreign handle refuse atomically");
 for(scenario=0;scenario<5;scenario++){
  RTMP_ADAPTER ad;struct wr_ft_iapp_request_state state,saved;
  struct wr_ft_iapp_token_handle early={0},claim={0};unsigned char wire[7],token[7]={8},mac[6]={66},bssid[6]={2};
  unsigned long serial;
  setup(&ad,&state,SST_NOT_AUTH,wire);
  assert(wr_ft_iapp_token_reserve_locked(&state.ledger,token,1,1,2,mac,bssid,&early));
  state.current[1]=early;state.detached[1]=1;
  serial=wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner);assert(serial);
  if(scenario==1)assert(wr_ft_iapp_token_claim_locked(&state.ledger,wire,ad.MacTab.Content[7].Addr,bssid,&claim));
  if(scenario==2)ad.wr_assoc_event_users[7]=1;
  if(scenario==3)state.current[7].serial++;
  saved=state;
  if(scenario){
   assert(!wr_ft_iapp_table_retire_locked(&ad,&state,scenario==4?serial+1:serial));
   assert(!memcmp(&state,&saved,sizeof(state)));
  }else{
   assert(wr_ft_iapp_table_retire_locked(&ad,&state,serial));
   assert(!state.current[1].serial&&!state.current[7].serial&&!state.preauth[7].serial);
   assert(state.ledger.next_serial==saved.ledger.next_serial);
   assert(!memcmp(state.token_counter,saved.token_counter,7));
   assert(!wr_ft_iapp_token_claim_locked(&state.ledger,token,mac,bssid,&claim));
  }
 }
 puts("PASS | FT full-table reset retirement | exact exclusive serial; all-slot preflight before mutation; late CLAIMED/busy/stale handle refuses atomically; token sequence retained");
 return 0;
}
