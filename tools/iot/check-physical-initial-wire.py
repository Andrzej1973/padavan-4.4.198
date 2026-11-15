"""Distinct initial-origin wire cannot be consumed as old CLOSE-origin wire."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#include <assert.h>
#include <string.h>
#include "physical-initial-wire.h"
int main(void){
 struct wr_iot_physical_initial_request q={.action=WR_STOP_ARM,.epoch=0x123456789ULL,
  .generation=0x234567890ULL,.idle_serial=0x345678901ULL,.nonce={7}};
 struct wr_iot_physical_initial_response got={0};unsigned char wire[64],saved[64];
 struct wr_iot_physical_stop_request old={0};
 assert(wr_iot_physical_initial_encode(wire,64,&q,0));memcpy(saved,wire,64);
 assert(wr_iot_physical_initial_decode(&got,wire,64,0));
 assert(!memcmp(&got.identity,&q,sizeof(q)));
 assert(!wr_iot_physical_initial_decode(&got,wire,64,1));
 assert(!wr_iot_physical_stop_request_decode(&old,wire,64));
 for(unsigned i=0;i<64;i++){
  memcpy(wire,saved,64);wire[i]^=1;
  if(i<5||i==6||i==7||i>=56)assert(!wr_iot_physical_initial_decode(&got,wire,64,0));
 }
 for(unsigned action=WR_STOP_ARM;action<=WR_STOP_RELEASE;action++){
  q.action=action;q.attempt=action==WR_STOP_ARM?0:0x456789012ULL;
  struct wr_iot_physical_initial_request reply=q;
  reply.attempt=0x456789012ULL;
  unsigned status=action==WR_STOP_ARM?WR_STOP_ARMED:action==WR_STOP_QUERY?WR_STOP_COMPLETE:
   action==WR_STOP_CANCEL?WR_STOP_CANCELLED:WR_STOP_RELEASED;
  assert(wr_iot_physical_initial_encode(wire,64,&reply,status));
  assert(wr_iot_physical_initial_decode(&got,wire,64,1));
  assert(wr_iot_physical_initial_reply_matches(&got,&q));
  assert(!wr_iot_physical_initial_decode(&got,wire,64,0));
  for(unsigned fault=0;fault<5;fault++){
   assert(wr_iot_physical_initial_decode(&got,wire,64,1));
   switch(fault){case 0:got.identity.epoch++;break;case 1:got.identity.generation++;break;
    case 2:got.identity.idle_serial++;break;case 3:got.identity.nonce[15]++;break;
    case 4:got.status=99;break;}
   assert(!wr_iot_physical_initial_reply_matches(&got,&q));
  }
 }
 struct wr_iot_physical_stop_request close={.action=WR_STOP_ARM,.epoch=1,.generation=2,
  .open_token=3,.closed_serial=4,.nonce={5}};
 assert(wr_iot_physical_stop_request_encode(wire,64,&close));
 assert(!wr_iot_physical_initial_decode(&got,wire,64,0));
 assert(!got.identity.epoch&&!got.status);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-initial-wire-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=10)
print('PASS initial-origin wire: separate discriminator from CLOSE,64-bit idle/attempt IDs, reserved bytes, strict action/status, stale reply refusal and cleared failures; endpoint uninstalled')
