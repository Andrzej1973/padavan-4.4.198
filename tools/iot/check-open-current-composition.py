#!/usr/bin/env python3
"""Compile actual transformed common entry; execute new route and old regressions."""
import runpy,subprocess,tempfile
from pathlib import Path
here=Path(__file__).parent
compose=runpy.run_path(str(here/'open-current-composition.py'))['compose']
original=(here/'driver-api-closed-entry.inc').read_text();generated=compose(original)
source=(here/'check-driver-api-closed-entry.c').read_text()
source=source.replace(' struct wr_iot_driver_owner wr_iot_driver_owner;',' struct wr_iot_driver_owner wr_iot_driver_owner;\n struct {int active;} wr_iot_close_owner;')
source=source.replace('#define VIRTUAL_IF_NUM(ad) 1U','#define VIRTUAL_IF_NUM(ad) test_vendor_count\nstatic unsigned test_vendor_count=1;')
source=source.replace('#include "driver-api-closed-entry.inc"',generated)
insert=r'''
 for(unsigned fault=0;fault<7;fault++){
  struct device main_dev={1},iot={1};struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  unsigned long sequence=0;unsigned char nonce[16]={1},wire[64];struct ifreq rq={wire};
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);
  m->published=r->published=1;m->phase=r->phase=WR_REF_OWNED;m->last_token=1;r->last_token=2;
  ad.wr_iot_driver_owner.receipt.device=&iot;ad.wr_iot_driver_owner.receipt.epoch=1;
  ad.wr_iot_driver_owner.receipt.generation=2;ad.wr_iot_driver_owner.receipt.open_token=2;
  ad.wr_iot_driver_owner.receipt.valid=1;ad.wr_iot_driver_owner.receipt.request_id[0]=1;
  permitted=rtnl=1;copies_in=copies_out=0;copy_in_error=copy_out_error=0;test_vendor_count=2;
  switch(fault){case 1:permitted=0;break;case 2:rtnl=0;break;case 3:copy_in_error=1;break;case 4:copy_out_error=1;break;case 5:ad.wr_iot_close_owner.active=1;break;case 6:ad.mt7603=0;break;}
  assert(wr_iot_driver_open_current_query_encode(wire,64,nonce));
  int result=wr_iot_driver_closed_ioctl(&ad,&iot,&rq);
  if(!fault){struct wr_iot_driver_open_current_result out;assert(!result&&wr_iot_driver_open_current_decode(&out,nonce,1,2,wire,64)&&out.open_token==2);}
  else assert(result<0);
  if(fault==1||fault==2||fault==6)assert(!copies_in&&!copies_out);
  assert(!ad.wr_iot_transition_lock);
 }
 test_vendor_count=1;permitted=rtnl=1;copy_in_error=copy_out_error=0;
'''
source=source.replace('int main(void){','int main(void){\n'+insert,1)
with tempfile.TemporaryDirectory(prefix='wr-current-entry-compose-') as d:
 path=Path(d)/'t.c';path.write_text(source);exe=Path(d)/'t'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(path),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
try:compose(generated)
except ValueError:pass
else:raise AssertionError('Duplicate composition accepted')
print('PASS actual new current-OPEN common dispatch: capability/RTNL before user copy, typed receipt and legacy CLOSED/refusal/uncertainty regressions')
