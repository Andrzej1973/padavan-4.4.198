#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "physical-stop-record.h"
int main(void)
{
 unsigned char nonce[16]={1},other[16]={2};int task,foreign;
 struct wr_iot_peer_close_executor executor={0};
 struct wr_iot_peer_table_owner table;
 wr_iot_peer_table_owner_init(&table);
 unsigned long table_serial=wr_iot_peer_table_begin(&table);
 assert(table_serial&&wr_iot_peer_table_close_seal(&table,table_serial));
 assert(wr_iot_peer_close_executor_enter(&executor,WR_PEER_CLOSE_LEGACY,0));
 assert(wr_iot_peer_close_executor_leave(&executor,WR_PEER_CLOSE_LEGACY,0,1,1));
 for(unsigned fault=0;fault<9;fault++){
  struct wr_iot_physical_stop_record s={0};
  assert(wr_iot_physical_stop_arm(&s,1,2,3,4,nonce,&task,&executor));
  assert(!wr_iot_physical_stop_arm(&s,1,2,3,4,nonce,&task,&executor));
  struct wr_iot_physical_stop_record saved=s;
  assert(!wr_iot_physical_stop_begin(&s,2,1,2,nonce,&task));
  assert(!wr_iot_physical_stop_begin(&s,1,9,2,nonce,&task));
  assert(!wr_iot_physical_stop_begin(&s,1,1,9,nonce,&task));
  assert(!wr_iot_physical_stop_begin(&s,1,1,2,other,&task));
  assert(!wr_iot_physical_stop_begin(&s,1,1,2,nonce,&foreign));
  assert(!memcmp(&s,&saved,sizeof(s)));
  assert(wr_iot_physical_stop_begin(&s,1,1,2,nonce,&task));
  assert(!wr_iot_physical_stop_release(&s,1,1,2,nonce,&task));
  assert(!wr_iot_physical_stop_cancel(&s,1,1,2,nonce,&task));
  struct wr_iot_peer_table_owner observed=table;
  struct wr_iot_peer_close_executor current=executor;
  if(fault==1)current.running=1;
  if(fault==2)observed.closed=0;
  if(fault==3)observed.active=1;
  if(fault==4)observed.retained=1;
  if(fault==5)observed.poisoned=1;
  if(fault==6)observed.transactions=1;
  saved=s;
  assert(!wr_iot_physical_stop_finish(&s,1,1,2,nonce,&foreign,1,&executor,&table,2));
  assert(!memcmp(&s,&saved,sizeof(s)));
  int done=wr_iot_physical_stop_finish(&s,1,1,2,nonce,&task,fault!=7,
    &current,&observed,fault==8?1:2);
  assert(done==(fault==0));
  saved=s;
  assert(wr_iot_physical_stop_observe(&s,1,1,2,3,4,nonce,&task)==(fault==0));
  assert(!wr_iot_physical_stop_observe(&s,1,1,2,4,4,nonce,&task));
  assert(!wr_iot_physical_stop_observe(&s,1,1,2,3,5,nonce,&task));
  assert(!wr_iot_physical_stop_observe(&s,2,1,2,3,4,nonce,&task));
  assert(!wr_iot_physical_stop_observe(&s,1,1,2,3,4,other,&task));
  assert(!memcmp(&s,&saved,sizeof(s)));

  if(fault){
   assert(s.phase==WR_PHYS_STOP_FAILED&&s.task==&task);
   assert(!wr_iot_physical_stop_release(&s,1,1,2,nonce,&task));
  }else{
   assert(!wr_iot_physical_stop_finish(&s,1,1,2,nonce,&task,1,&current,&observed,2));
   assert(wr_iot_physical_stop_release(&s,1,1,2,nonce,&task)&&s.serial==1);
   assert(!wr_iot_physical_stop_observe(&s,1,1,2,3,4,nonce,&task));
   assert(!wr_iot_physical_stop_arm(&s,1,2,3,4,nonce,&task,&executor)&&s.serial==1);
   assert(wr_iot_physical_stop_arm(&s,1,2,3,4,other,&task,&executor)&&s.serial==2);
   assert(!wr_iot_physical_stop_begin(&s,1,1,2,nonce,&task));
  }
 }
 struct wr_iot_physical_stop_record cancelled={0};
 assert(wr_iot_physical_stop_arm(&cancelled,1,2,3,4,nonce,&task,&executor));
 assert(!wr_iot_physical_stop_cancel(&cancelled,1,1,2,nonce,&foreign));
 assert(wr_iot_physical_stop_cancel(&cancelled,1,1,2,nonce,&task));
 assert(cancelled.serial==1&&!cancelled.task&&cancelled.phase==WR_PHYS_STOP_IDLE);
 assert(!wr_iot_physical_stop_cancel(&cancelled,1,1,2,nonce,&task));
 assert(!wr_iot_physical_stop_arm(&cancelled,1,2,3,4,nonce,&task,&executor));
 assert(wr_iot_physical_stop_arm(&cancelled,1,2,3,4,other,&task,&executor));
 assert(!wr_iot_physical_stop_begin(&cancelled,1,1,2,nonce,&task));
 struct wr_iot_physical_stop_record exhausted={.serial=~0ULL};
 assert(!wr_iot_physical_stop_arm(&exhausted,1,2,3,4,nonce,&task,&executor));
 puts("PASS unbound physical-stop record: identity/task/serial stale refusal, actual executor/table conditions required,8 failures retain owner, no serial reuse; no RF/DMA or driver-binding proof");
}
