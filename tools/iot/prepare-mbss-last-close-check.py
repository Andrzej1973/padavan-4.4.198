#!/usr/bin/env python3
"""Final MBSS last-close through candidate physical chain; lower IO injected."""
import argparse,subprocess,sys
from pathlib import Path
import close_fixture_support as support
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():raise SystemExit('New fixture required')
intermediate=a.output.with_suffix('.chain.c')
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-close-chain-check.py')),str(a.driver),str(intermediate)],check=True)
s=intermediate.read_text();s=s[:s.index('int main(void){')]
s='#include "interface-registry.h"\n'+s
old='void *net_dev;} RTMP_ADAPTER;'
if s.count(old)!=1:raise SystemExit('Changed chain fixture adapter')
s=s.replace(old,'void *net_dev;int wr_iot_ticket_wait;struct wr_iot_interface_ref wr_iot_interface_refs[2];} RTMP_ADAPTER;')
extra=r'''
#define WDEV_NUM_MAX 1
#define wake_up_all(queue) (++*(queue))
typedef struct net_device *PNET_DEV;
static int module_refs,mbss_calls;
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) ((void)(dev),assert(!held))
#define RT_MOD_DEC_USE_COUNT() (--module_refs)
static int MBSS_Close(PNET_DEV dev){assert(dev&&!held);mbss_calls++;return 0;}
'''
close=(a.driver/'include/wr-iot-mbss-close-checked.inc').read_text()
post=r'''
int main(void){
 RTMP_ADAPTER a={0};struct net_device main_dev={&a},dev={&a};struct wr_iot_radio_ticket t;
 unsigned long generation;
 struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
 wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;a.wr_iot_transition.main_inhibited=1;a.wr_iot_transition.serial=1;a.VirtualIfCnt=1;a.net_dev=&main_dev;
 wr_iot_ref_init(r,&dev,1);r->published=1;assert(wr_iot_ref_reserve(r,&dev,1,1));assert(wr_iot_ref_open_finish(r,&dev,1,1,1));module_refs=1;
 r->family=WR_REF_FAMILY_MBSS;
 assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0&&generation==r->generation);join_result=1;
 assert(wr_iot_mbss_close_checked(&dev,r->generation,&t)==-1&&!a.VirtualIfCnt&&module_refs==1&&r->phase==WR_REF_CLOSING&&r->close_stage==3&&mbss_calls==1&&!post_calls);
 join_result=0;assert(wr_iot_mbss_close_checked(&dev,r->generation,&t)==0&&!module_refs&&r->phase==WR_REF_IDLE&&mbss_calls==1&&pre_calls==1&&post_calls==1);
 assert(a.wr_iot_ticket_wait==1);
 assert(wr_iot_mbss_close_checked(&dev,r->generation,&t)==0&&!module_refs&&mbss_calls==1&&joins==2);
 wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;a.wr_iot_transition.serial=1;a.VirtualIfCnt=1;
 wr_iot_ref_init(r,&dev,2);r->published=1;assert(wr_iot_ref_reserve(r,&dev,2,1));assert(wr_iot_ref_open_finish(r,&dev,2,1,1));module_refs=1;radio_result=0;
 r->family=WR_REF_FAMILY_MBSS;
 assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0&&generation==r->generation);int prior_pci=pci_calls,prior_mbss=mbss_calls;
 assert(wr_iot_mbss_close_checked(&dev,r->generation,&t)==-1&&module_refs==1&&r->phase==WR_REF_CLOSING&&a.wr_iot_transition.shutdown_stage==3&&pci_calls==prior_pci+1);
 assert(wr_iot_mbss_close_checked(&dev,r->generation,&t)==-1&&module_refs==1&&pci_calls==prior_pci+1&&mbss_calls==prior_mbss+1&&!held);
 assert(a.wr_iot_ticket_wait==1);
 return 0;
}
'''
if 'BOOLEAN APShutdown(' in (a.driver/'include/ap.h').read_text():
 refusal=r'''
 {
 RTMP_ADAPTER failed={0};struct net_device fm={&failed},fd={&failed};struct wr_iot_radio_ticket ft;
 struct wr_iot_interface_ref *fr=&failed.wr_iot_interface_refs[0];unsigned long fg;
 int oldap=ap_calls,oldjoin=joins,oldpost=post_calls,oldrings=ring_frees,oldmbss=mbss_calls;
 wr_iot_radio_transition_init(&failed.wr_iot_transition);failed.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;
 failed.wr_iot_transition.main_inhibited=1;failed.wr_iot_transition.serial=1;failed.VirtualIfCnt=1;failed.net_dev=&fm;
 wr_iot_ref_init(fr,&fd,3);fr->published=1;assert(wr_iot_ref_reserve(fr,&fd,3,1));
 assert(wr_iot_ref_open_finish(fr,&fd,3,1,1));fr->family=WR_REF_FAMILY_MBSS;module_refs=1;
 assert(wr_iot_mbss_begin_close(&fd,&ft,&fg)==0);ap_result=0;radio_result=1;join_result=0;
 assert(wr_iot_mbss_close_checked(&fd,fg,&ft)==-1&&!held&&module_refs==1);
 assert(fr->phase==WR_REF_CLOSING&&fr->close_stage==3&&!failed.VirtualIfCnt);
 assert(failed.wr_iot_transition.shutdown_stage==3U&&!failed.wr_iot_transition.close_notified);
 assert(ap_calls==oldap+1&&mbss_calls==oldmbss+1&&joins==oldjoin&&post_calls==oldpost&&ring_frees==oldrings);
 ap_result=1;assert(wr_iot_mbss_close_checked(&fd,fg,&ft)==-1&&module_refs==1&&!held);
 assert(ap_calls==oldap+1&&mbss_calls==oldmbss+1&&post_calls==oldpost&&failed.wr_iot_ticket_wait==0);
 }
'''
 post=post.replace(' return 0;',refusal+' return 0;',1)
if support.enabled(a.driver):post=support.fresh(post)
a.output.write_text(s+extra+close+post)
print('Extracted final MBSS last-close/physical chain; joins and hardware injected')
