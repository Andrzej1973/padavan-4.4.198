#!/usr/bin/env python3
"""Compose actual record, pin return, lifetime and terminal reply functions."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-physical-stop-pins.c').read_text().split('int main(void){',1)[0]
body=r'''
struct pid {unsigned refs;};
static struct pid pid_owner={1},pid_foreign={1};
static struct pid *task_pid(struct task_struct*t){return t==&owner?&pid_owner:&pid_foreign;}
static struct pid *get_pid(struct pid*p){assert(!locked&&p->refs);p->refs++;return p;}
static void put_pid(struct pid*p){assert(!locked&&p->refs>1);p->refs--;}
#include "physical-stop-terminal.inc"
int main(void){
 for(unsigned action=WR_STOP_CANCEL;action<=WR_STOP_RELEASE;action++){
  struct net_device dev={1};
  struct wr_iot_physical_stop_pins local={0},slot={0},detached={0};
  struct wr_iot_physical_stop_record record={0};
  struct wr_iot_peer_close_executor executor={0};
  struct wr_iot_radio_transition radio;wr_iot_radio_transition_init(&radio);
  radio.phase=WR_RADIO_READY;radio.main_ready=1;
  struct wr_iot_physical_stop_lifetime lifetime={0};
  struct wr_iot_physical_stop_terminal cache={0};
  struct wr_iot_physical_stop_request request={.action=action,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=1,.nonce={1}};
  unsigned char wire[64];current=&owner;module_refs=1;fail_module=locked=0;
  assert(!wr_iot_physical_stop_pins_acquire(&local,&foreign,&dev));
  assert(wr_iot_physical_stop_lifetime_begin(&lifetime,&radio)==1);
  return_lifetime=&lifetime;
  assert(wr_iot_physical_stop_pins_acquire(&local,current,&dev));
  locked=1;
  assert(wr_iot_physical_stop_pins_publish(&slot,&local,&record,1,2,3,4,request.nonce,&executor));
  assert(wr_iot_physical_stop_blocks_retirement(&record,&slot));
  if(action==WR_STOP_RELEASE){
   assert(wr_iot_physical_stop_begin(&record,1,1,2,request.nonce,current));
   struct wr_iot_peer_table_owner table;wr_iot_peer_table_owner_init(&table);
   unsigned long serial=wr_iot_peer_table_begin(&table);assert(serial&&wr_iot_peer_table_close_seal(&table,serial));
   assert(wr_iot_physical_stop_finish(&record,1,1,2,request.nonce,current,1,&executor,&table,2));
  }
  locked=0;
  assert(wr_iot_physical_stop_terminal_prepare(&cache,&request));
  locked=1;
  assert(wr_iot_physical_stop_pins_detach(&slot,&detached,&record,1,1,2,request.nonce,action==WR_STOP_CANCEL));
  assert(!wr_iot_physical_stop_terminal_commit(&cache,record.phase==WR_PHYS_STOP_IDLE,module_refs==1,!lifetime.active));
  assert(!wr_iot_physical_stop_terminal_reply(&cache,&request,wire,64));
  locked=0;dropping=&detached;
  assert(wr_iot_physical_stop_pins_drop(&detached));
  assert(module_refs==1&&owner.refs==1&&dev.refs==1&&lifetime.active);
  locked=1;
  assert(wr_iot_physical_stop_lifetime_end(&lifetime,1,record.phase==WR_PHYS_STOP_IDLE,!detached.module&&!detached.task&&!detached.device));
  assert(wr_iot_physical_stop_terminal_commit(&cache,record.phase==WR_PHYS_STOP_IDLE,module_refs==1&&owner.refs==1&&dev.refs==1,!lifetime.active));
  locked=0;return_lifetime=NULL;
  /* Lost initial user copy: retry only serializes cache, no second cleanup. */
  for(unsigned retry=0;retry<3;retry++){
   assert(wr_iot_physical_stop_terminal_reply(&cache,&request,wire,64));
   struct wr_iot_physical_stop_response reply;
   assert(wr_iot_physical_stop_response_decode(&reply,wire,64,&request));
   assert(reply.status==(action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED));
   assert(module_refs==1&&owner.refs==1&&dev.refs==1&&pid_owner.refs==2);
  }
  assert(!wr_iot_physical_stop_pins_detach(&slot,&detached,&record,1,1,2,request.nonce,action==WR_STOP_CANCEL));
  assert(wr_iot_physical_stop_terminal_clear(&cache)&&pid_owner.refs==1);
 }
 puts("PASS actual cancel/release terminal composition: record detach -> real pin returns -> lifetime end -> reply, premature publication refuses, lost-copy retries never rerun cleanup; kernel operations injected");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='iot-stop-terminal-compose-') as d:
    unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
