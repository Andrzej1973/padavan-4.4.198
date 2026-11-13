#!/usr/bin/env python3
"""Execute experimental common release dispatcher with injected executor."""
from pathlib import Path
import runpy
import subprocess
import tempfile

here = Path(__file__).resolve().parent
compose = runpy.run_path(str(here / 'release-dispatch-composition.py'))['compose']
original = (here / 'driver-api-closed-entry.inc').read_text()
generated = compose(original)
for broken in (generated, original.replace('if(!rtnl_is_locked())return -EBUSY;', ''),
               original.replace('if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;', '')):
    try:
        compose(broken)
    except ValueError:
        pass
    else:
        raise AssertionError('Changed common boundary accepted')
source = (here / 'check-driver-api-closed-entry.c').read_text()
binding = r'''
#include "driver-api-open-recovery-wire.h"
static int wr_iot_driver_open_recovery_reply(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 unsigned char nonce[16];
 assert(rtnl&&permitted&&copies_in&&!ad->wr_iot_transition_lock);
 if(!wr_iot_driver_open_recovery_query_decode(nonce,wire,64))return -EINVAL;
 if(ad->ApCfg.BssidNum!=3||ad->ApCfg.MBSSID[2].wdev.if_dev!=dev)return -EAGAIN;
 if(!wr_iot_driver_open_recovery_encode(wire,64,nonce,1,2,3))return -EINVAL;
 return copy_to_user(rq->ifr_data,wire,64)?-EFAULT:0;
}

#include "driver-api-close-release-wire.h"
static unsigned releases;
static int wr_iot_driver_close_release(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 assert(rtnl&&permitted&&copies_in&&!ad->wr_iot_transition_lock);
 if(ad->ApCfg.BssidNum!=3||ad->ApCfg.MBSSID[2].wdev.if_dev!=dev||
    request->adapter_epoch!=1||request->device_generation!=2||
    request->open_token!=3||request->open_request_id[0]!=1)return -ESTALE;
 releases++;return 0;
}
'''
# The actual binding is separately compiled/executed by its dedicated fixture.
generated = generated.replace('#include "driver-api-close-release-binding.inc"', '')
generated = generated.replace('#include "driver-api-open-recovery-entry.inc"', '')
source = source.replace('#include "driver-api-closed-entry.inc"', binding + generated)
cases = r'''
 for(unsigned fault=0;fault<11;fault++){
  struct device main_dev={1},iot={0},guest={1};
  struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  struct wr_iot_driver_close_request request={{1},1,2,3};
  unsigned char wire[64];assert(wr_iot_driver_close_release_encode(wire,64,&request));
  struct ifreq rq={wire};PNET_DEV target=&iot;
  rtnl=permitted=1;copy_in_error=copy_out_error=0;copies_in=copies_out=releases=0;
  switch(fault){
   case 1:rtnl=0;break;case 2:permitted=0;break;case 3:ad.mt7603=0;break;
   case 4:copy_in_error=1;break;case 5:wire[0]=0;break;
   case 6:wire[63]=1;break;case 7:wire[24]=2;break;
   case 8:wire[4]=13;break;case 9:target=&guest;break;
   case 10:ad.ApCfg.BssidNum=4;break;
  }
  int result=wr_iot_driver_closed_ioctl(&ad,target,&rq);
  assert((result==0)==(fault==0));assert(releases==(fault==0));
  if(fault>=1&&fault<=3)assert(!copies_in);
  assert(!copies_out&&!ad.wr_iot_transition_lock&&main_dev.running&&guest.running);
 }
 for(unsigned fault=0;fault<9;fault++){
  struct device main_dev={1},iot={0},guest={1};
  struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  unsigned char wire[64],nonce[16]={1};struct ifreq rq={wire};PNET_DEV target=&iot;
  assert(wr_iot_driver_open_recovery_query_encode(wire,64,nonce));
  rtnl=permitted=1;copy_in_error=copy_out_error=0;copies_in=copies_out=0;
  switch(fault){
   case 1:rtnl=0;break;case 2:permitted=0;break;case 3:ad.mt7603=0;break;
   case 4:copy_in_error=1;break;case 5:wire[63]=1;break;
   case 6:target=&guest;break;case 7:ad.ApCfg.BssidNum=4;break;
   case 8:copy_out_error=1;break;
  }
  int status=wr_iot_driver_closed_ioctl(&ad,target,&rq);
  assert((status==0)==(fault==0));
  if(fault>=1&&fault<=3)assert(!copies_in);
  if(!fault){
   struct wr_iot_driver_open_recovery_result reply;
   assert(wr_iot_driver_open_recovery_decode(&reply,nonce,1,2,wire,64)&&reply.open_token==3);
  }
 }
 rtnl=permitted=1;copy_in_error=copy_out_error=0;
'''
source = source.replace('int main(void){', 'int main(void){\n' + cases, 1)
with tempfile.TemporaryDirectory(prefix='wr-release-dispatch-') as scratch:
    path = Path(scratch) / 'test.c'
    executable = Path(scratch) / 'test'
    path.write_text(source)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(here), str(path), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
print('PASS actual release common entry: privilege before copy, wire validation, executor refusal and legacy queries; executor injected')
