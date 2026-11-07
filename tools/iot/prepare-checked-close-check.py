#!/usr/bin/env python3
"""Extract final assembled checked close into synthetic AP/PCI host fixture."""
import argparse,re
from pathlib import Path
import close_fixture_support as support
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():raise SystemExit('New fixture output required')
s=(a.driver/'common/rtmp_init_inf.c').read_text(encoding='utf-8');sig='INT wr_iot_drv_close_checked('
if support.enabled(a.driver):sig='static INT wr_iot_checked_close_body('
if s.count(sig)!=1:raise SystemExit('Expected one final checked-close function')
start=s.index(sig);end=s.index('\n}',start)+2;f=s[start:end]
bound=re.search(r'if\s*\(\s*(?:wr_iot_dequeue_polls|waited)\+\+\s*>=\s*1000U\s*\)',f)
if (not bound or
    bound.start()>
    f.index('wr_iot_mgmt_exit_checked(pAd,ticket)')):
 raise SystemExit('Checked close must bound dequeue polling before management join')
template=Path(__file__).with_name('checked-close-host-fixture.c.in').read_text(encoding='utf-8')
if template.count('@@CHECKED_CLOSE_FUNCTION@@')!=1:raise SystemExit('Changed fixture marker')
ap=(a.driver/'ap/ap.c').read_text()
if 'BOOLEAN APShutdown(' in ap:
 ap_start=ap.index('BOOLEAN APShutdown(');ap_end=ap.index('\n}',ap_start)+2
 shutdown=ap[ap_start:ap_end]
 template=template.replace('#define APShutdown(ad) ((void)(ad),mock_ap_shutdown())','')
 template=template.replace('static int mock_ap_shutdown(void){assert(!held);ap_calls++;return ap_result;}','')
 template=template.replace('int wr_iot_transition_lock;','int wr_iot_transition_lock,MacTabLock;')
 shim='''
static int ap_lock_frees;
#define MlmeRadioOff(ad) ((void)(ad),assert(!held),ap_calls++)
#define APStop(ad) ((void)(ad),ap_result)
#define NdisFreeSpinLock(lock) ((void)(lock),ap_lock_frees++)
'''
 f=shim+shutdown+'\n'+f
 refusal=r'''
static void check_ap_shutdown_refusal(void){
 RTMP_ADAPTER a={0};struct wr_iot_radio_ticket t;
 int before_ap=ap_calls,before_locks=ap_lock_frees,before_pre=pre_calls;
 int before_join=joins,before_post=post_calls,before_rings=ring_frees,before_pci=pci_calls;
 wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_READY;
 assert(wr_iot_radio_begin_stop(&a.wr_iot_transition,1,&t));
 ap_result=0;join_result=0;radio_result=1;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE&&!held);
 assert(a.wr_iot_transition.shutdown_stage==3U&&ap_calls==before_ap+1);
 assert(ap_lock_frees==before_locks&&pre_calls==before_pre&&joins==before_join);
 assert(post_calls==before_post&&ring_frees==before_rings&&pci_calls==before_pci);
 ap_result=1;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE&&!held);
 assert(ap_calls==before_ap+1&&ap_lock_frees==before_locks&&joins==before_join);
 assert(post_calls==before_post&&ring_frees==before_rings&&pci_calls==before_pci);
}
'''
 template=template.replace('int main(void){',refusal+'\nint main(void){',1)
 template=template.replace('check_dequeue_timeout();return 0;}','check_dequeue_timeout();check_ap_shutdown_refusal();return 0;}',1)
if support.enabled(a.driver):
 before,after=template.split('@@CHECKED_CLOSE_FUNCTION@@')
 # Keep the actual APShutdown and its injected dependencies from the old setup.
 shutdown_prefix=f[:f.index('static INT wr_iot_checked_close_body(')]
 a.output.write_text(support.prefix(before)+shutdown_prefix+support.definitions(s)+support.fresh(after),encoding='utf-8')
else:a.output.write_text(template.replace('@@CHECKED_CLOSE_FUNCTION@@',f),encoding='utf-8')
print('Extracted final checked close; AP/PCI primitives injected, not target proof')
