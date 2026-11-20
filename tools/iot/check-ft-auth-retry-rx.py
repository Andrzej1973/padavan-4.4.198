#!/usr/bin/env python3
"""Execute prepared AUTH retry RX selector and generated enqueue together."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-auth-rx-queue.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
enqueue=runpy.run_path(str(here/'ft-auth-enqueue-composition.py'))
changed,rp=enqueue['compose_retry'](data['native'])
start=changed.rindex('BOOLEAN wr_ft_auth_retry_enqueue_for_recv(')
retry=changed[start:changed.index('\n}',start)+2]
rx=runpy.run_path(str(here/'ft-auth-rx-composition.py'))
prepared=rx['compose_retry'](data['source'],rp)
try:rx['compose_retry'](prepared,rp)
except ValueError:pass
else:raise AssertionError('duplicate RX retry accepted')
start=prepared.index('BOOLEAN MlmeEnqueueForRecv(')
wrapper=prepared[start:prepared.index('\n}',start)+2]
prefix=data['prefix'].replace('typedef struct {unsigned ft_pending_generation,',
 'typedef struct {unsigned ft_preauth_serial,ft_preauth_generation,ft_preauth_wcid,ft_preauth_bss;unsigned char ft_preauth_mac[6],ft_preauth_bssid[6];unsigned ft_pending_generation,',1)
prefix=prefix.replace('#include "peer-table-owner.h"',
 '#include "peer-table-owner.h"\n#include "peer-close-executor.h"\n#include "ft-iapp-request-state.h"')
prefix=prefix.replace('int MacTabLock,OpMode;',
 'struct wr_ft_iapp_request_state wr_ft_iapp_requests;struct wr_iot_peer_close_executor wr_iot_peer_close_executor;int MacTabLock,OpMode;')
prefix=prefix.replace('struct wifi_dev{unsigned char bssid[6];};',
 'struct wifi_dev{unsigned char bssid[6];unsigned func_idx;};')
prefix+='''
#define SST_NOT_AUTH 0
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 ad->wr_assoc_visible[entry->wcid]=entry->assoc_gen;
 memcpy(ad->wr_assoc_addr[entry->wcid],entry->Addr,6);
}
#include "ft-auth-retry-peer-scope.h"
'''
main=data['main'][:data['main'].index('int main(void)')]+r'''
int main(void){
 for(int scenario=0;scenario<8;scenario++){
 RTMP_ADAPTER ad={0};FRAME_802_11 frame={0};struct raw_rssi_info rssi={0};
 ad.OpMode=OPMODE_AP;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[7];
 *e=(MAC_TABLE_ENTRY){.assoc_gen=3,.wcid=7,.func_tb_idx=2,.Sst=SST_NOT_AUTH,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 ad.wr_assoc_generations[7]=ad.wr_assoc_visible[7]=3;ad.wr_assoc_addr[7][0]=42;
 struct wr_ft_preauth_identity identity={.serial=17,.generation=3,.wcid=7,.bss=2,.mac={42},.bssid={2}};
 ad.wr_ft_iapp_requests.preauth[7]=identity;
 frame.Hdr.FC.Type=FC_TYPE_MGMT;frame.Hdr.FC.SubType=SUBTYPE_AUTH;
 frame.Hdr.Addr1[0]=2;frame.Hdr.Addr2[0]=42;frame.Octet[0]=2;frame.Octet[2]=1;
 hook=&ad;replace_before_queue=0;
 if(scenario==1)ad.wr_ft_iapp_requests.preauth[7].serial=0;
 if(scenario==2)ad.wr_ft_iapp_requests.preauth[7].generation++;
 if(scenario==3)e->wdev=&ad.ApCfg.MBSSID[0].wdev;
 if(scenario==4)ad.MacTab.Content[6]=*e;
 if(scenario==5)ad.wr_assoc_event_users[7]=1;
 if(scenario==6)replace_before_queue=1;
 if(scenario==7)ad.Mlme.Queue.Num=4;
 int result=RX(30,&frame);
 if(scenario!=0&&scenario!=6){assert(!result);continue;}
 assert(result);
 MLME_QUEUE_ELEM *event=&ad.Mlme.Queue.Entry[0];
 assert(event->ft_preauth_serial==17&&event->ft_preauth_generation==3&&event->assoc_gen==3);
 struct wr_ft_pending_peer_scope scope={0};MAC_TABLE_ENTRY *entry=NULL;
 NdisAcquireSpinLock(&ad.MacTabLock);
 int entered=wr_ft_auth_retry_enter_locked(&ad,&ad.wr_ft_iapp_requests,event,2,frame.Hdr.Addr2,&scope,&entry);
 if(scenario==6)assert(!entered&&!entry&&!scope.active);
 else {assert(entered&&entry==e);assert(wr_ft_pending_peer_leave_locked(&ad,&scope));}
 NdisReleaseSpinLock(&ad.MacTabLock);
 assert(!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
 }
 puts("PASS | AUTH retry RX-to-queue-to-lease | exact preauth selector; missing/stale/foreign/inactive duplicate/busy/full refusal; captured serial retained across queue-lock reuse; stale callback refused; default/EAP/SNR");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-retry-rx-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text(prefix+data['fallback']+data['active']+data['pending']+retry+wrapper+main)
 for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
  subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
