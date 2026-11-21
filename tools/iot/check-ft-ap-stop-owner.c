#include <assert.h>
#include <stdio.h>
#include "ft-ap-stop-owner.h"
int main(void){
 int device,other;
 {
  struct wr_ft_ap_stop_owner owner={0};
  struct wr_ft_ap_stop_identity id={&device,6,8,1,0},foreign=id;
  struct wr_iot_peer_table_owner table,wrong_table;
  unsigned long serial;
  wr_iot_peer_table_owner_init(&table);
  serial=wr_iot_peer_table_begin(&table);assert(serial);
  assert(wr_iot_peer_table_finish(&table,serial,0));
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(wr_ft_ap_stop_bind(&owner,&id,41));
  assert(wr_ft_ap_stop_reset_bind(&owner,&id,serial,64,8));
  assert(!wr_ft_ap_stop_table_hold(&owner,&id,&table,serial));
  for(unsigned int phase=WR_FT_AP_RESET_PREPARED;
      phase<=WR_FT_AP_RESET_APCLI;phase++)
   assert(wr_ft_ap_stop_reset_advance(&owner,&id,serial,
       (enum wr_ft_ap_reset_phase)phase));
  assert(owner.reset_phase==WR_FT_AP_RESET_TABLE);
  assert(wr_ft_ap_stop_table_hold(&owner,&id,&table,serial));
  assert(!wr_ft_ap_stop_enter(&owner,&id));
  assert(!wr_ft_ap_stop_table_resume(&owner,&id,&table,serial+1));
  foreign.generation++;
  assert(!wr_ft_ap_stop_table_resume(&owner,&foreign,&table,serial));
  foreign=id;
  wrong_table=table;wrong_table.serial++;
  assert(!wr_ft_ap_stop_table_resume(&owner,&id,&wrong_table,serial));
  assert(table.retained&&!wr_iot_peer_table_allows(&table,serial));
  assert(wr_ft_ap_stop_table_resume(&owner,&id,&table,serial));
  assert(table.active&&!table.retained&&owner.running);
  assert(!wr_iot_peer_table_allows(&table,0));
  assert(!wr_iot_peer_table_transaction_enter(&table));
  assert(!wr_ft_ap_stop_table_resume(&owner,&id,&table,serial));
  assert(wr_iot_peer_table_finish(&table,serial,1));
 }
 {
  struct wr_ft_ap_stop_owner owner={0};
  struct wr_ft_ap_stop_identity id={&device,5,7,1,0};
  struct wr_ft_ap_wds_identity wds={&other,3,11,1,9,{1,2,3,4,5,6}};
  struct wr_iot_peer_table_owner table;
  unsigned long serial;
  wr_iot_peer_table_owner_init(&table);
  serial=wr_iot_peer_table_begin(&table);assert(serial);
  assert(wr_iot_peer_table_finish(&table,serial,0));
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(wr_ft_ap_stop_bind(&owner,&id,40));
  assert(wr_ft_ap_stop_reset_bind(&owner,&id,serial,64,8));
  for(unsigned int phase=WR_FT_AP_RESET_PREPARED;
      phase<=WR_FT_AP_RESET_APCLI;phase++)
   assert(wr_ft_ap_stop_reset_advance(&owner,&id,serial,
       (enum wr_ft_ap_reset_phase)phase));
  assert(owner.reset_phase==WR_FT_AP_RESET_TABLE);
  assert(wr_ft_ap_stop_wds_begin(&owner,&id,serial,&wds));
  assert(!wr_ft_ap_stop_table_hold(&owner,&id,&table,serial));
  assert(owner.running&&owner.wds_valid&&table.retained);
 }
 for(unsigned int stop=0;stop<=3;stop++){
  struct wr_ft_ap_stop_owner owner={0};
  struct wr_ft_ap_stop_identity id={&device,7,9,2,0},foreign=id;
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(!wr_ft_ap_stop_enter(&owner,&id));
  assert(!wr_ft_ap_stop_advance(&owner,&id,0));
  assert(wr_ft_ap_stop_bind(&owner,&id,42));
  for(unsigned int i=0;i<stop;i++)assert(wr_ft_ap_stop_advance(&owner,&id,i));
  assert(wr_ft_ap_stop_yield(&owner,&id));
  for(unsigned int field=0;field<5;field++){
   foreign=id;
   if(field==0)foreign.device=&other;
   if(field==1)foreign.operation++;
   if(field==2)foreign.generation++;
   if(field==3)foreign.bss++;
   if(field==4)foreign.whole_adapter=1;
   assert(!wr_ft_ap_stop_enter(&owner,&foreign));
  }
  assert(owner.cache_ticket==42&&owner.stage==stop);
  assert(wr_ft_ap_stop_enter(&owner,&id));
  if(stop<3)assert(!wr_ft_ap_stop_finish(&owner,&id));
  for(unsigned int i=stop;i<3;i++)assert(wr_ft_ap_stop_advance(&owner,&id,i));
  assert(wr_ft_ap_stop_finish(&owner,&id)&&!owner.active&&!owner.cache_ticket);
 }
 {
  struct wr_ft_ap_stop_owner owner={0};
  struct wr_ft_ap_stop_identity id={&device,8,10,2,0};
  struct wr_ft_ap_wds_identity wds={&other,4,12,1,9,{0,1,2,3,4,5}},wrong;
  struct wr_ft_ap_wds_identity wds2={&other,4,14,3,10,{0,1,2,3,4,7}};
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(wr_ft_ap_stop_bind(&owner,&id,43));
  for(unsigned int i=0;i<3;i++)assert(wr_ft_ap_stop_advance(&owner,&id,i));
  assert(wr_ft_ap_stop_reset_bind(&owner,&id,55,64,8));
  assert(!wr_ft_ap_stop_reset_bind(&owner,&id,56,64,8));
  assert(!wr_ft_ap_stop_reset_bind(&owner,&id,55,1,8));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_PREPARED));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_IRQ_OFF));
  assert(wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_WDS,1));
  assert(!wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_WDS,0));
  assert(!wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_WDS,9));
  wrong=wds;wrong.index=8;
  assert(!wr_ft_ap_stop_wds_begin(&owner,&id,55,&wrong));
  wrong=wds;wrong.wcid=64;
  assert(!wr_ft_ap_stop_wds_begin(&owner,&id,55,&wrong));
  assert(wr_ft_ap_stop_wds_begin(&owner,&id,55,&wds));
  wrong=wds;wrong.address[5]++;
  assert(!wr_ft_ap_stop_wds_not_written(&owner,&id,55,&wrong));
  assert(wr_ft_ap_stop_wds_not_written(&owner,&id,55,&wds));
  assert(!wr_ft_ap_stop_enter(&owner,&id));
  assert(!wr_ft_ap_stop_wds_resume(&owner,&id,56,&wds));
  assert(!wr_ft_ap_stop_wds_resume(&owner,&id,55,&wrong));
  assert(wr_ft_ap_stop_wds_resume(&owner,&id,55,&wds));
  assert(wr_ft_ap_stop_wds_applied(&owner,&id,55,&wds));
  assert(wr_ft_ap_stop_wds_complete(&owner,&id,55,&wds));
  assert(wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_WDS,2));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_WDS));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_APCLI));
  assert(wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_TABLE,3));
  assert(!wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_TABLE,65));
  assert(wr_ft_ap_stop_wds_begin(&owner,&id,55,&wds2));
  assert(wr_ft_ap_stop_wds_not_written(&owner,&id,55,&wds2));
  assert(wr_ft_ap_stop_wds_resume(&owner,&id,55,&wds2));
  assert(wr_ft_ap_stop_wds_applied(&owner,&id,55,&wds2));
  assert(wr_ft_ap_stop_wds_complete(&owner,&id,55,&wds2));
  assert(wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_TABLE,4));
  assert(wr_ft_ap_stop_yield(&owner,&id));
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(wr_ft_ap_stop_reset_bind(&owner,&id,55,64,8));
  assert(owner.reset_phase==WR_FT_AP_RESET_TABLE&&owner.reset_cursor==4);
  assert(wr_ft_ap_stop_reset_cursor(&owner,&id,55,WR_FT_AP_RESET_TABLE,5));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_TABLE));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,55,WR_FT_AP_RESET_FINAL));
  assert(wr_ft_ap_stop_finish(&owner,&id));
 }
 {
  struct wr_ft_ap_stop_owner owner={0};
  struct wr_ft_ap_stop_identity id={&device,9,11,2,0};
  struct wr_ft_ap_wds_identity wds={&other,4,13,2,10,{0,1,2,3,4,5}};
  assert(wr_ft_ap_stop_enter(&owner,&id));
  assert(wr_ft_ap_stop_bind(&owner,&id,44));
  for(unsigned int i=0;i<3;i++)assert(wr_ft_ap_stop_advance(&owner,&id,i));
  assert(wr_ft_ap_stop_reset_bind(&owner,&id,57,64,8));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,57,WR_FT_AP_RESET_PREPARED));
  assert(wr_ft_ap_stop_reset_advance(&owner,&id,57,WR_FT_AP_RESET_IRQ_OFF));
  assert(wr_ft_ap_stop_wds_begin(&owner,&id,57,&wds));
  assert(wr_ft_ap_stop_wds_uncertain(&owner,&id,57,&wds,WR_FT_AP_WDS_PARTIAL));
  assert(!wr_ft_ap_stop_enter(&owner,&id));
  assert(!wr_ft_ap_stop_wds_resume(&owner,&id,57,&wds));
  assert(!wr_ft_ap_stop_finish(&owner,&id));
 }
 puts("PASS | FT AP stop owner | exact operation/BSS/generation, retained-table exact-serial resume, ordinary writers blocked, WDS NOT_WRITTEN-only replay, PARTIAL refusal; native binding pending");return 0;
}
