"""Compare pure deferred WAN plan with extracted pinned SDK branch behavior."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include "restart-wan-plan.h"
/* Branch transcription of check_apcli_wan after SDK interface resolution. */
static int sdk(int ap,int man,int wisp,int band,int on){
 if(ap)return WR_WAN_NONE;
 band&=1;
 if(man!=wisp)return WR_WAN_FULL_RESTART;
 else if(on&&wisp==band)return WR_WAN_RECONNECT;
 return WR_WAN_NONE;
}
int main(void){
 for(int ap=0;ap<2;ap++)for(int man=-1;man<2;man++)for(int wisp=-1;wisp<2;wisp++)
 for(int band=0;band<2;band++)for(int on=0;on<2;on++)
  assert((int)wr_iot_restart_wan_plan(ap,man,wisp,band,on)==sdk(ap,man,wisp,band,on));
 assert(wr_iot_restart_wan_plan(0,-2,-1,0,1)==WR_WAN_INVALID);
 assert(wr_iot_restart_wan_plan(0,-1,2,0,1)==WR_WAN_INVALID);
 assert(wr_iot_restart_wan_plan(0,-1,-1,2,1)==WR_WAN_INVALID);
 assert(wr_iot_restart_wan_plan(0,-1,-1,0,2)==WR_WAN_INVALID);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wan-plan-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',str(p),'-I'+str(here),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS WAN follow-up planner:72 valid AP/MAN/WISP/band/radio combinations match transcribed SDK branches, invalid identities refuse; no SDK resolution/dispatch/runtime claim')
