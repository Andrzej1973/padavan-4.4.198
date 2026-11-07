#!/usr/bin/env python3
"""Extract both real close bodies and shared wrappers; inject competing calls."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('predecessor',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
base=a.output.with_name(a.output.name+'.base.c')
if a.output.exists() or base.exists():p.error('new outputs required')
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-peer-close-path-check.py')),
 str(a.predecessor),str(base)],check=True)
prefix=base.read_text().split('INT wr_iot_drv_close_checked(')[0]
prefix=prefix.replace('#include "peer-table-owner.h"','#include "peer-table-owner.h"\n#include "peer-close-executor.h"')
prefix=prefix.replace('unsigned int wr_iot_peer_legacy_close_state;',
 'unsigned int wr_iot_peer_legacy_close_state;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_close_executor wr_iot_peer_close_executor;')
prefix=prefix.replace('static void check_reserved(RTMP_ADAPTER *ad){', '''
INT RTMPDrvClose(VOID *,VOID *);
INT wr_iot_drv_close_checked(VOID *,VOID *,const struct wr_iot_radio_ticket *);
static struct wr_iot_radio_ticket competing_ticket;
static unsigned int competing_rejections;
static void check_reserved(RTMP_ADAPTER *ad){
 assert(RTMPDrvClose(ad,NULL)==NDIS_STATUS_FAILURE);
 assert(wr_iot_drv_close_checked(ad,NULL,&competing_ticket)==NDIS_STATUS_FAILURE);
 competing_rejections+=2;
''')
source=(a.candidate/'common/rtmp_init_inf.c').read_text()
def extract(sig):
 start=source.index(sig);return source[start:source.index('\n}',start)+2]
legacy=extract('static INT wr_iot_legacy_close_body(')
checked=extract('static INT wr_iot_checked_close_body(')
post='''
static void ready(RTMP_ADAPTER *a,struct wr_iot_radio_ticket *t){
 memset(a,0,sizeof *a);wr_iot_radio_transition_init(&a->wr_iot_transition);
 wr_iot_peer_table_owner_init(&a->wr_iot_peer_table_owner);
 wr_iot_peer_close_executor_init(&a->wr_iot_peer_close_executor);
 a->wr_iot_transition.phase=WR_RADIO_READY;
 assert(wr_iot_radio_begin_stop(&a->wr_iot_transition,1,t));competing_ticket=*t;
}
int main(void){RTMP_ADAPTER a;struct wr_iot_radio_ticket t,bad;int before;
 ready(&a,&t);join_result=1;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(a.wr_iot_peer_close_executor.retained&&!a.wr_iot_peer_close_executor.running);
 before=pre_calls;assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&pre_calls==before);
 bad=t;bad.serial++;
 assert(wr_iot_drv_close_checked(&a,NULL,&bad)==NDIS_STATUS_FAILURE);
 assert(a.wr_iot_peer_close_executor.serial==t.serial);
 join_result=0;assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_SUCCESS);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 assert(a.wr_iot_peer_table_owner.closed&&competing_rejections>=8);
 ready(&a,&t);bad=t;bad.operation=WR_RADIO_RESET;
 assert(wr_iot_drv_close_checked(&a,NULL,&bad)==NDIS_STATUS_FAILURE);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 ap_result=0;assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE);
 before=ap_calls;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==before);
 ready(&a,&t);ap_result=1;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_SUCCESS);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 before=ap_calls;assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_SUCCESS&&ap_calls==before);
 assert(!held);return 0;}
'''
if 'wr_iot_peer_table_owner.transactions' in (a.candidate/'include/wr-iot-peer-close-executor.inc').read_text():
 post=post.replace(' assert(!held);return 0;}', '''
 ready(&a,&t);a.wr_iot_peer_table_owner.transactions=1;before=ap_calls;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 assert(!held);return 0;}''')
if 'wr_iot_peer_delete_active' in (a.candidate/'include/wr-iot-peer-close-executor.inc').read_text():
 post=post.replace(' assert(!held);return 0;}', '''
 ready(&a,&t);a.wr_iot_peer_delete_active=1;before=ap_calls;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 assert(!held);return 0;}''')
if 'wr_iot_peer_table_owner.active' in (a.candidate/'include/wr-iot-peer-close-executor.inc').read_text():
 post=post.replace(' assert(!held);return 0;}', '''
 ready(&a,&t);before=ap_calls;
 assert(wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner));
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE&&ap_calls==before);
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 assert(!held);return 0;}''')
a.output.write_text(prefix+'\n#include "wr-iot-peer-legacy-close.inc"\n'
 '#define RtmpMgmtTaskExit(ad) (check_reserved(ad),joins++)\n'+legacy+'\n'+checked+
 '\n#include "wr-iot-peer-close-executor.inc"\n'+post,encoding='utf-8')
print('Extracted both close bodies/wrappers with deterministic competing-call hooks; hardware mocked')
