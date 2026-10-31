#!/usr/bin/env python3
"""Extract checked close plus real table helpers into a synthetic host fixture."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--legacy', action='store_true')
a = p.parse_args()
if a.output.exists():
    p.error('new fixture output required')
source = (a.driver / 'common/rtmp_init_inf.c').read_text()
start = source.index('INT RTMPDrvClose(' if a.legacy else 'INT wr_iot_drv_close_checked(')
function = source[start:source.index('\n}', start) + 2]
template = Path(__file__).with_name('checked-close-host-fixture.c.in').read_text()
template = template[:template.index('static void check_dequeue_timeout(')]
template = template.replace('#define MAC_TABLE int', '''
#include "peer-table-owner.h"
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
typedef unsigned int UINT;
typedef struct {int live;} MAC_TABLE_ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} STA_TR_ENTRY;
typedef struct {unsigned int Size;MAC_TABLE_ENTRY Content[4];STA_TR_ENTRY tr_entry[3];} MAC_TABLE;
#define IS_ENTRY_NONE(e) (!(e)->live)
''')
template = template.replace('int MacTab;', 'MAC_TABLE MacTab;int MacTabLock;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;unsigned long wr_iot_peer_close_serial;unsigned int wr_iot_peer_legacy_close_state;')
template = template.replace('#define MlmeHalt(ad) ((void)(ad),assert(!held),pre_calls++)', '#define MlmeHalt(ad) (check_reserved(ad),pre_calls++)')
template = template.replace('#define RTMPFreeTxRxRingMemory(ad) ((void)(ad),ring_frees++)', '#define RTMPFreeTxRxRingMemory(ad) (check_reserved(ad),ring_frees++)')
template = template.replace('#define UserCfgExit(ad) ((void)(ad),assert(!held),post_calls++)', '#define UserCfgExit(ad) (check_reserved(ad),post_calls++)')
anchor = 'static int wr_iot_mgmt_exit_checked('
index = template.index(anchor)
template = template[:index] + '''
#define NdisAcquireSpinLock(lock) ((void)(lock),assert(!held),held=1)
#define NdisReleaseSpinLock(lock) ((void)(lock),assert(held),held=0)
#include "wr-iot-peer-close-table.inc"
static void check_reserved(RTMP_ADAPTER *ad){
 assert(!held&&ad->wr_iot_peer_close_serial);
 NdisAcquireSpinLock(&ad->MacTabLock);
 assert(!wr_iot_peer_table_begin(&ad->wr_iot_peer_table_owner));
 assert(!wr_iot_peer_table_begin_open(&ad->wr_iot_peer_table_owner));
 assert(!wr_iot_peer_table_transaction_enter(&ad->wr_iot_peer_table_owner));
 NdisReleaseSpinLock(&ad->MacTabLock);
}
''' + template[index:]
template = template.replace('assert(!held&&ad&&t);joins++;', 'assert(!held&&ad&&t);check_reserved(ad);joins++;')
template = template.replace('@@CHECKED_CLOSE_FUNCTION@@', function)
post = '''
static void ready(RTMP_ADAPTER *a,struct wr_iot_radio_ticket *t){
 memset(a,0,sizeof *a);wr_iot_radio_transition_init(&a->wr_iot_transition);
 wr_iot_peer_table_owner_init(&a->wr_iot_peer_table_owner);
 a->wr_iot_transition.phase=WR_RADIO_READY;
 assert(wr_iot_radio_begin_stop(&a->wr_iot_transition,1,t));
}
int main(void){
 RTMP_ADAPTER a;struct wr_iot_radio_ticket t;unsigned long serial;int oldap,oldpre,oldjoin;
 ready(&a,&t);join_result=1;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 serial=a.wr_iot_peer_close_serial;assert(serial&&a.wr_iot_transition.shutdown_stage==1);
 assert(pre_calls==1&&post_calls==0&&ring_frees==0&&ap_calls==1);
 join_result=0;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_SUCCESS);
 assert(!a.wr_iot_peer_close_serial&&a.wr_iot_peer_table_owner.closed);
 assert(pre_calls==1&&post_calls==1&&ring_frees==1&&ap_calls==1&&joins==2);
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_SUCCESS&&joins==2);
 assert(!wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner));
 assert(wr_iot_peer_table_begin_open(&a.wr_iot_peer_table_owner)>serial);
 ready(&a,&t);a.wr_iot_peer_table_owner.transactions=1;
 oldap=ap_calls;oldpre=pre_calls;oldjoin=joins;
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(a.wr_iot_transition.shutdown_stage==3&&ap_calls==oldap+1);
 assert(pre_calls==oldpre&&joins==oldjoin&&!a.wr_iot_peer_close_serial);
 assert(wr_iot_drv_close_checked(&a,NULL,&t)==NDIS_STATUS_FAILURE);
 assert(ap_calls==oldap+1&&pre_calls==oldpre&&joins==oldjoin);
 assert(!held);return 0;
}
'''
if a.legacy:
    # Legacy management completion remains a mocked synchronous call.
    pos = template.index('static int wr_iot_mgmt_exit_checked(')
    end = template.index('\n', pos)
    template = template[:pos] + template[end + 1:]
    template = template.replace(function, '#include "wr-iot-peer-legacy-close.inc"\n#define RtmpMgmtTaskExit(ad) (check_reserved(ad),joins++)\n' + function)
    post = '''
int main(void){
 RTMP_ADAPTER a={0};int oldap,oldpre,oldrings,oldjoins;
 (void)join_result;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);
 ap_result=0;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE);
 assert(a.wr_iot_peer_legacy_close_state==1U&&ap_calls==1&&!pre_calls);
 ap_result=1;assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==1);
 memset(&a,0,sizeof a);radio_result=1;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_SUCCESS);
 assert(a.wr_iot_peer_legacy_close_state==2U&&a.wr_iot_peer_table_owner.closed);
 oldap=ap_calls;oldpre=pre_calls;oldrings=ring_frees;oldjoins=joins;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_SUCCESS);
 assert(ap_calls==oldap&&pre_calls==oldpre&&ring_frees==oldrings&&joins==oldjoins);
 memset(&a,0,sizeof a);radio_result=0;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE);
 assert(a.wr_iot_peer_legacy_close_state==1U&&ring_frees==oldrings);
 oldap=ap_calls;oldjoins=joins;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==oldap&&joins==oldjoins);
 memset(&a,0,sizeof a);radio_result=1;a.DeQueueRunning[0]=1;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&a.wr_iot_peer_legacy_close_state==1U);
 assert(delay_calls>=1000&&ap_calls==oldap);
 a.DeQueueRunning[0]=0;
 assert(RTMPDrvClose(&a,NULL)==NDIS_STATUS_FAILURE&&ap_calls==oldap);
 assert(!held);return 0;
}
'''
template += post
a.output.write_text(template, encoding='utf-8')
print('Extracted checked-close/table helpers; APShutdown and hardware primitives mocked')
