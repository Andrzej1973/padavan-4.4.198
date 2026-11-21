"""Proposed DOWN syntax; separate from READY idle and owned IoT CLOSE."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#include <assert.h>
#include <string.h>
#include "precreated-down-wire.h"
int main(void){
 unsigned char nonce[16]={1},got[16],wire[64],valid[64];struct wr_iot_down_result out;
 assert(wr_iot_down_query_encode(wire,64,nonce)&&wr_iot_down_query_decode(got,wire,64)&&!memcmp(nonce,got,16));
 assert(!wr_iot_idle_query_decode(got,wire,64));
 assert(wr_iot_down_reply_encode(wire,64,nonce,0x100000002ULL,0x200000003ULL,0x300000004ULL));memcpy(valid,wire,64);
 assert(wr_iot_down_reply_decode(&out,nonce,wire,64)&&out.epoch==0x100000002ULL&&out.generation==0x200000003ULL&&out.main_close_serial==0x300000004ULL);
 struct wr_iot_idle_result idle;assert(!wr_iot_idle_reply_decode(&idle,nonce,wire,64));
 for(unsigned i=0;i<64;i++){
  if((i>=24&&i<48))continue;
  wire[i]^=1;out.epoch=out.generation=out.main_close_serial=7;
  assert(!wr_iot_down_reply_decode(&out,nonce,wire,64)&&!out.epoch&&!out.generation&&!out.main_close_serial);memcpy(wire,valid,64);
 }
 for(unsigned i=24;i<48;i+=8){memset(wire+i,0,8);assert(!wr_iot_down_reply_decode(&out,nonce,wire,64));memcpy(wire,valid,64);}
 assert(!wr_iot_down_reply_decode(&out,nonce,wire,63));
 assert(!wr_iot_down_reply_decode(&out,0,wire,64));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-down-wire-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS proposed DOWN codec: full64 identities, distinct READY-idle opcode, nonce/reserved/zero/short rejection and cleared output; no route or lifecycle permission')
