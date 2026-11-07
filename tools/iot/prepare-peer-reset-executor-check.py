#!/usr/bin/env python3
"""Exercise the actual candidate reset fragment with close-executor contention."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new fixture output required')
fragment=(a.candidate/'include/wr-iot-reset-admission.inc').read_text()
if 'WR_PEER_CLOSE_RESET' not in fragment or 'wr_iot_peer_close_executor_leave' not in fragment:
 p.error('candidate does not bind reset executor')
s=Path(__file__).with_name('check-reset-admission.c').read_text()
s=s.replace('static int held,pse,pdma,again,rtnl_held,wakes;',
 'static int held,pse,pdma,again,rtnl_held,wakes,break_ticket;')
s=s.replace('#include "radio-transition.h"','#include "radio-transition.h"\n#include "peer-close-executor.h"\n#include "peer-table-owner.h"')
s=s.replace('int wr_iot_transition_lock;',
 'int wr_iot_transition_lock;int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_close_executor wr_iot_peer_close_executor;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;')
s=s.replace('#define WR_IOT_RESET_TEST', '''
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define WR_IOT_RESET_TEST''')
s=s.replace('pdma++;}', '''pdma++;
 assert(ad->wr_iot_peer_close_executor.running);
 assert(ad->wr_iot_peer_close_executor.lane==WR_PEER_CLOSE_RESET);
 NdisAcquireSpinLock(&ad->MacTabLock);
 assert(!wr_iot_peer_close_executor_enter(&ad->wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0));
 assert(!wr_iot_peer_close_executor_enter(&ad->wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44));
 NdisReleaseSpinLock(&ad->MacTabLock);
 if(break_ticket)ad->wr_iot_transition.serial++;
}''')
s=s.replace('#include "reset-admission.inc"','#include "wr-iot-reset-admission.inc"')
s=s.replace(' wr_iot_radio_request_close(&a.wr_iot_transition);', '''
 assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0));
 PDMAResetAndRecovery(&a);
 assert(pdma==4&&a.wr_iot_transition.reset_pending&&!rtnl_held&&!held);
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0,1,1));
 wr_iot_radio_reset_drain(&a);assert(pdma==5&&wakes==5);
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44));
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44,0,1));
 PSEResetAndRecovery(&a);
 assert(pse==1&&pdma==5&&a.wr_iot_transition.reset_pending&&!rtnl_held&&!held);
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44));
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44,1,1));
 wr_iot_radio_reset_drain(&a);assert(pse==2&&pdma==6&&wakes==6);
 wr_iot_radio_request_close(&a.wr_iot_transition);''')
s=s.replace('assert(pse==1&&pdma==4&&!held&&!rtnl_held&&wakes==4);',
 'assert(pse==2&&pdma==6&&!held&&!rtnl_held&&wakes==6);\n assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));')
s=s.replace(' puts(', '''
 RTMP_ADAPTER broken={0};
 wr_iot_radio_transition_init(&broken.wr_iot_transition);
 broken.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;break_ticket=1;
 PDMAResetAndRecovery(&broken);
 assert(broken.wr_iot_peer_close_executor.retained&&!broken.wr_iot_peer_close_executor.running);
 assert(wakes==6&&!held&&!rtnl_held);
 assert(!wr_iot_peer_close_executor_enter(&broken.wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0));
 assert(!wr_iot_peer_close_executor_enter(&broken.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,44));
 puts(''')
if 'wr_iot_peer_table_owner.transactions' in fragment:
 s=s.replace(' RTMP_ADAPTER broken={0};', '''
 RTMP_ADAPTER writer={0};int before_pdma=pdma;
 wr_iot_radio_transition_init(&writer.wr_iot_transition);
 writer.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;
 {unsigned long owner=wr_iot_peer_table_begin(&writer.wr_iot_peer_table_owner);assert(owner);
 PDMAResetAndRecovery(&writer);
 assert(pdma==before_pdma&&writer.wr_iot_transition.reset_pending);
 assert(wr_iot_peer_table_finish(&writer.wr_iot_peer_table_owner,owner,1));}
 writer.wr_iot_peer_table_owner.transactions=1;
 PDMAResetAndRecovery(&writer);
 assert(pdma==before_pdma&&writer.wr_iot_transition.reset_pending);
 assert(wr_iot_peer_close_executor_idle(&writer.wr_iot_peer_close_executor));
 writer.wr_iot_peer_table_owner.transactions=0;
 wr_iot_radio_reset_drain(&writer);assert(pdma==before_pdma+1);
 RTMP_ADAPTER broken={0};''')
 s=s.replace('assert(wakes==6&&!held&&!rtnl_held);','assert(wakes==7&&!held&&!rtnl_held);')
if 'wr_iot_peer_delete_active' in fragment:
 s=s.replace(' writer.wr_iot_peer_table_owner.transactions=1;', '''
 writer.wr_iot_peer_delete_active=1;PDMAResetAndRecovery(&writer);
 assert(pdma==before_pdma&&writer.wr_iot_transition.reset_pending);
 writer.wr_iot_peer_delete_active=0;
 writer.wr_iot_peer_table_owner.transactions=1;''')
a.output.write_text(s,encoding='utf-8')
print('Prepared actual candidate reset fragment with close-executor contention checks')
