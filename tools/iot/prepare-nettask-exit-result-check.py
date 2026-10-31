#!/usr/bin/env python3
"""Inject failed net-task exit into both real close bodies; verify no later teardown."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('predecessor',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();base=a.output.with_name(a.output.name+'.base.c')
if a.output.exists() or base.exists():p.error('new fixture outputs required')
root=a.candidate
assert 'INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);' in (root/'include/rtmp.h').read_text()
for rel in ['os/linux/rt_rbus_pci_drv.c','os/linux/rt_sdio.c']:
 s=(root/rel).read_text();start=s.index('INT RtmpNetTaskExit(');body=s[start:s.index('\n}',start)+2]
 assert 'return NDIS_STATUS_SUCCESS;' in body
s=(root/'common/rtmp_init_inf.c').read_text()
assert 'err2:\n\tif (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) return FALSE;' in s
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-peer-close-executor-check.py')),
 str(a.predecessor),str(root),str(base)],check=True)
s=base.read_text();start=s.index('static INT wr_iot_legacy_close_body(')
s=s[:start]+'''static int nettask_result,nettask_calls;
#undef RtmpNetTaskExit
#define RtmpNetTaskExit(ad) ((void)(ad),assert(!held),nettask_calls++,nettask_result)
'''+s[start:]
s=s[:s.index('int main(void){')]+'''
int main(void){RTMP_ADAPTER a;struct wr_iot_radio_ticket t;int oldap;
 ready(&a,&t);nettask_result=NDIS_STATUS_FAILURE;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(nettask_calls==1&&!pre_calls&&!joins&&!post_calls&&!ring_frees);
 assert(a.wr_iot_transition.shutdown_stage==3&&a.wr_iot_peer_close_executor.retained);
 oldap=ap_calls;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(nettask_calls==1&&ap_calls==oldap&&!pre_calls);
 ready(&a,&t);
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE);
 assert(nettask_calls==2&&!pre_calls&&!joins&&!post_calls&&!ring_frees);
 oldap=ap_calls;assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE);
 assert(nettask_calls==2&&ap_calls==oldap);
 ready(&a,&t);nettask_result=NDIS_STATUS_SUCCESS;join_result=0;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_SUCCESS);
 assert(nettask_calls==3&&pre_calls==1&&post_calls==1&&ring_frees==1);
 assert(!held);return 0;}
'''
a.output.write_text(s,encoding='utf-8')
print('Extracted actual close guards with net-task failure injection; init guard and bus signatures source checked')
