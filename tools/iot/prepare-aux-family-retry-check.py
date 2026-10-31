#!/usr/bin/env python3
"""Extend actual OPEN/CLOSE cycle with same-ticket retry, without family/HNAT replay."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent;base=a.output.with_name(a.output.name+'.cycle-base.c')
if a.output.exists() or base.exists():p.error('new outputs required')
subprocess.run([sys.executable,str(here/'prepare-aux-open-close-cycle-check.py'),str(a.candidate),str(base)],check=True)
s=base.read_text();wrappers=''
for name,fn in [('ap/ap_apcli_inf.c','ApCli_VirtualIF_Close_Retry'),('os/linux/rt_profile.c','Monitor_VirtualIF_Close_Retry')]:
 text=(a.candidate/name).read_text();start=text.index('INT '+fn+'(')
 wrappers+=text[start:text.index('\n}',start)+2]+'\n'
s=s.replace('int main(void){',wrappers+'int main(void){',1)
anchor='  cycle_ready(&ad,f,dev);open_family_result=1;'
if s.count(anchor)!=1:p.error('changed cycle fixture')
tests=r'''
  cycle_ready(&ad,f,dev);
  assert((monitor?Monitor_VirtualIF_Open(&dev[1]):ApCli_VirtualIF_Open(&dev[1]))==0);
  down_result=1;
  assert((monitor?Monitor_VirtualIF_Close(&dev[1]):ApCli_VirtualIF_Close(&dev[1]))==-EBUSY);
  assert(pins==1&&ad.count==2&&family_calls==1&&down_calls==1);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_DOWN_RETRY);
  unsigned long serial=ad.wr_iot_interface_refs[1].close_serial;
  int old_hnat=hnat;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY);
  assert(pins==1&&ad.count==2&&family_calls==1&&down_calls==2&&hnat==old_hnat);
  assert(ad.wr_iot_family_close[1].phase==WR_FAMILY_DOWN_RETRY);
  assert(ad.wr_iot_interface_refs[1].close_stage==1);
  ad.wr_iot_interface_refs[1].generation++;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY&&down_calls==2);
  ad.wr_iot_interface_refs[1].generation--;
  ad.wr_iot_interface_refs[1].last_token++;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY&&down_calls==2);
  ad.wr_iot_interface_refs[1].last_token--;
  ad.wr_iot_transition.epoch++;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY&&down_calls==2);
  ad.wr_iot_transition.epoch--;
  down_result=0;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==0);
  assert(!pins&&ad.count==1&&family_calls==1&&down_calls==3&&hnat==old_hnat);
  assert(ad.wr_iot_interface_refs[1].phase==WR_REF_IDLE);
  assert(ad.wr_iot_interface_refs[1].close_serial==serial&&ad.wr_iot_family_close[1].serial==serial);
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY&&down_calls==3);
'''
s=s.replace(anchor,tests+anchor,1)
anchor='  assert(pins==1&&ad.count==2&&family_calls==1&&open_family_calls==1);'
if s.count(anchor)!=1:p.error('changed failed-family fixture')
s=s.replace(anchor,anchor+'''
  int before_retry=down_calls;
  assert((monitor?Monitor_VirtualIF_Close_Retry(&dev[1]):ApCli_VirtualIF_Close_Retry(&dev[1]))==-EBUSY);
  assert(down_calls==before_retry&&family_calls==1&&pins==1&&ad.count==2);
''',1)
a.output.write_text(s,encoding='utf-8')
print('Composed actual same-ticket retry with OPEN/CLOSE cycle and stale-identity refusal')
