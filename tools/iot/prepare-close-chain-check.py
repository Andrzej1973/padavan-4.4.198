#!/usr/bin/env python3
"""Final-source chain host fixture; worker/hardware injected, not target proof."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():raise SystemExit('New output required')
template=Path(__file__).with_name('checked-close-host-fixture.c.in').read_text()
prefix=template.split('@@CHECKED_CLOSE_FUNCTION@@')[0]
old='int infType;} RTMP_ADAPTER;'
if prefix.count(old)!=1:raise SystemExit('Changed fixture type')
prefix=prefix.replace(old,'int infType;unsigned int VirtualIfCnt;void *net_dev;} RTMP_ADAPTER;\ntypedef RTMP_ADAPTER *PRTMP_ADAPTER;\nstruct net_device {PRTMP_ADAPTER priv;};')
prefix+='\n#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->priv)\n#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)\n#define VIRTUAL_IF_DEC(ad) ((ad)->VirtualIfCnt--)\n'
s=(a.driver/'common/rtmp_init_inf.c').read_text();sig='INT wr_iot_drv_close_checked('
if s.count(sig)!=1:raise SystemExit('Changed checked close')
start=s.index(sig);f=s[start:s.index('\n}',start)+2]
bridge=(a.driver/'include/wr-iot-physical-close-result.inc').read_text()
down=(a.driver/'include/wr-iot-virtual-down.inc').read_text()
cfg=(a.driver/'common/cmm_cfg.c').read_text()
if '\n#include "wr-iot-virtual-down.inc"\n' not in cfg:raise SystemExit('Missing actual newline/include')
post=r'''
int main(void){
 RTMP_ADAPTER a={0};struct net_device dev={&a};struct wr_iot_radio_ticket t,bad;
 wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_READY;a.VirtualIfCnt=1;a.net_dev=&dev;
 assert(wr_iot_radio_begin_stop(&a.wr_iot_transition,1,&t));join_result=1;
 assert(wr_iot_virtual_down_checked(&a,&t)==1&&!a.VirtualIfCnt&&pre_calls==1&&!post_calls&&a.wr_iot_transition.virtual_down_stage==1);
 bad=t;bad.serial++;assert(wr_iot_virtual_down_checked(&a,&bad)==1&&joins==1);
 join_result=0;assert(wr_iot_virtual_down_checked(&a,&t)==0&&!a.VirtualIfCnt&&pre_calls==1&&post_calls==1&&a.wr_iot_transition.virtual_down_stage==2);
 assert(wr_iot_virtual_down_checked(&a,&t)==0&&joins==2&&post_calls==1);
 wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_READY;a.VirtualIfCnt=1;assert(wr_iot_radio_begin_stop(&a.wr_iot_transition,1,&t));radio_result=0;
 int oldpost=post_calls,oldpci=pci_calls;
 assert(wr_iot_virtual_down_checked(&a,&t)==1&&!a.VirtualIfCnt&&a.wr_iot_transition.shutdown_stage==3&&post_calls==oldpost&&pci_calls==oldpci+1);
 assert(wr_iot_virtual_down_checked(&a,&t)==1&&pci_calls==oldpci+1&&!held);
 return 0;
}
'''
a.output.write_text(prefix+f+'\n'+bridge+'\n'+down+post)
print('Extracted final close chain; worker and hardware operations injected')
