#!/usr/bin/env python3
"""Execute the generated common entry, actual CLOSE/progress replies and old queries."""
from pathlib import Path
import argparse
import runpy
import subprocess
import tempfile

here = Path(__file__).resolve().parent
compose = runpy.run_path(str(here / 'close-dispatch-composition.py'))['compose']
original = (here / 'driver-api-closed-entry.inc').read_text()
generated = compose(original)
for broken in [generated, original.replace('if(!rtnl_is_locked())return -EBUSY;', ''),
               original.replace('if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;', '')]:
    try:
        compose(broken)
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate or missing common boundary accepted')
generated = runpy.run_path(str(here / 'open-current-composition.py'))['compose'](generated)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--driver', type=Path)
args = parser.parse_args()
if args.driver:
    assert (args.driver / 'include/driver-api-closed-entry.inc').read_text() == generated
    entry = (args.driver / 'os/linux/rt_main_dev.c').read_text()
    assert entry.index('#include "driver-api-close-bundle.h"') < entry.index('#include "driver-api-closed-entry.inc"')
    assert 'if(cmd==WR_IOT_DRIVER_IOCTL_CLOSED_CONFIG)return wr_iot_driver_closed_ioctl(ad,net_dev,rq);' in entry
    assert 'netDevHook.ioctl = rt28xx_ioctl;' in (args.driver / 'ap/ap_mbss_inf.c').read_text()

source = (here / 'check-driver-api-closed-entry.c').read_text()
source = source.replace(' struct wr_iot_driver_owner wr_iot_driver_owner;',
                        ' struct wr_iot_driver_owner wr_iot_driver_owner;\n struct {int active;} wr_iot_close_owner;')
bindings = r'''
#include "driver-api-close-progress-wire.h"
static unsigned close_enters,close_calls,progress_calls;
static int wr_iot_driver_close_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *r,const void *task){
 assert(ad&&dev&&task&&!ad->wr_iot_transition_lock&&rtnl&&permitted);
 if(r->adapter_epoch!=1||r->device_generation!=2||r->open_token!=3||r->open_request_id[0]!=1)return -ESTALE;
 close_enters++;return 0;
}
static int dev_close(PNET_DEV dev){assert(rtnl&&dev->running);close_calls++;dev->running=0;return 0;}
static int wr_iot_driver_close_finish_recover(RTMP_ADAPTER *ad,PNET_DEV dev,
 const void *task,int status,int *handoff){assert(ad&&dev&&task&&!status);*handoff=0;return 1;}
static int wr_iot_driver_close_progress(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *r){
 assert(ad&&dev&&!ad->wr_iot_transition_lock&&rtnl&&permitted);
 if(r->adapter_epoch!=1||r->device_generation!=2||r->open_token!=3||r->open_request_id[0]!=1)return -ESTALE;
 progress_calls++;return -EINPROGRESS;
}
#define current ((const void *)1)
#include "driver-api-close-entry.inc"
#include "driver-api-close-progress-entry.inc"
'''
source = source.replace('#include "driver-api-closed-entry.inc"', bindings + generated)
cases = r'''
 for(unsigned mode=0;mode<2;mode++)for(unsigned fault=0;fault<17;fault++){
  struct device main_dev={1},iot={1},guest={1};
  struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  struct wr_iot_driver_close_request request={{1},1,2,3};unsigned char wire[64];
  assert(mode?wr_iot_driver_close_progress_encode(wire,64,&request):
              wr_iot_driver_close_request_encode(wire,64,&request));
  struct ifreq rq={wire};PNET_DEV target=&iot;
  permitted=rtnl=1;copy_in_error=copy_out_error=0;copies_in=copies_out=0;
  close_enters=close_calls=progress_calls=0;
  switch(fault){
   case 1:rtnl=0;break;case 2:permitted=0;break;case 3:ad.mt7603=0;break;
   case 4:copy_in_error=1;break;case 5:ad.ApCfg.BssidNum=2;break;
   case 6:ad.ApCfg.BssidNum=4;break;case 7:target=&main_dev;break;
   case 8:target=&guest;break;case 9:wire[63]=1;break;
   case 10:wire[3]='1';break;case 11:wire[24]=2;break;
   case 12:iot.running=0;break;case 13:wire[4]=99;break;
   case 14:wire[32]=3;break;case 15:wire[40]=4;break;
   case 16:wire[8]=2;break;
  }
  int result=wr_iot_driver_closed_ioctl(&ad,target,&rq);
  if(fault==0||(mode&&fault==12)){
   assert(result==(mode?-EINPROGRESS:0));
   assert(close_calls==!mode&&close_enters==!mode&&progress_calls==mode);
  }else assert(result<0&&!close_calls&&!close_enters&&!progress_calls);
  if(fault==1||fault==2||fault==3)assert(!copies_in);
  assert(!copies_out&&!ad.wr_iot_transition_lock&&main_dev.running&&guest.running);
 }
 permitted=rtnl=1;copy_in_error=copy_out_error=0;
'''
source = source.replace('int main(void){', 'int main(void){\n' + cases, 1)
with tempfile.TemporaryDirectory(prefix='wr-close-dispatch-') as scratch:
    root = Path(scratch)
    (root / 'test.c').write_text(source)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(here), str(root / 'test.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True)
print('PASS generated CLOSE/progress common routes, exact BSS, capability/copy/identity failures, progress while DOWN and legacy queries; executor/syscalls injected')
