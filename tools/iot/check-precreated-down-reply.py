"""Actual internal reply builder plus reference/peer binding; no ioctl route."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
s=(here/'check-precreated-down-binding.c').read_text()
s=s.replace('#include "precreated-down-binding.inc"','#include "precreated-down-binding.inc"\n#include "precreated-down-reply.inc"')
s=s.replace('static int held,rtnl=1,running,locks,drift_peer;', 'static int drift_identity;static int held,rtnl=1,running,locks,drift_peer;')
s=s.replace('locks++;if(drift_peer', 'locks++;if(drift_identity&&locks==5){if(drift_identity==1)drift_adapter->wr_iot_transition.epoch++;else drift_adapter->wr_iot_main_recovery.last_release.ticket.serial++;}if(drift_peer')
a=' drift_peer=0;ad=before;'
b=a+r'''
 unsigned char nonce[16]={1},wire[64];struct wr_iot_down_result result;
 assert(wr_iot_down_query_encode(wire,64,nonce));
 assert(!wr_iot_precreated_down_reply(&ad,&iot_device,wire,64,wire));
 assert(wr_iot_down_reply_decode(&result,nonce,wire,64)&&result.epoch==radio.epoch&&result.generation==i->generation&&result.main_close_serial==7);
 assert(!memcmp(&ad,&before,sizeof(ad)));
 for(drift_identity=1;drift_identity<=2;drift_identity++){
  locks=0;drift_adapter=&ad;assert(wr_iot_down_query_encode(wire,64,nonce));
  assert(wr_iot_precreated_down_reply(&ad,&iot_device,wire,64,wire)==-EAGAIN);
  for(unsigned n=0;n<64;n++){assert(!wire[n]);}ad=before;
 }
 drift_identity=0;
 assert(wr_iot_down_query_encode(wire,64,nonce));wire[63]=1;
 assert(wr_iot_precreated_down_reply(&ad,&iot_device,wire,64,wire)==-EINVAL);
 for(unsigned n=0;n<64;n++)assert(!wire[n]);
 assert(wr_iot_down_query_encode(wire,64,nonce));ad.wr_iot_control_users=1;
 assert(wr_iot_precreated_down_reply(&ad,&iot_device,wire,64,wire)==-EAGAIN);
 for(unsigned n=0;n<64;n++){assert(!wire[n]);}ad=before;
 assert(wr_iot_down_query_encode(wire,64,nonce));rtnl=0;
 assert(wr_iot_precreated_down_reply(&ad,&iot_device,wire,64,wire)==-EBUSY);rtnl=1;
'''
assert s.count(a)==1;s=s.replace(a,b)
with tempfile.TemporaryDirectory(prefix='wr-down-reply-') as d:
 p=Path(d)/'check.c';p.write_text(s);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual DOWN reply/ref/peer binding: nonce echo/Main close identity, alias safety, malformed/control/RTNL refusal clears output, no mutation; no ioctl route')
