#!/usr/bin/env python3
"""Execute prepared over-air FT AUTH RX wrapper with controlled queue actors."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-rx-generation.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):fixture=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
module=runpy.run_path(str(here/'ft-auth-rx-composition.py'))
prepared=module['compose'](fixture['mlme'],fixture['active_proto'].replace('wr_ft_mlme_enqueue_for_recv','wr_ft_auth_mlme_enqueue_for_recv'),fixture['pending_proto'].replace('wr_ft_pending_enqueue_for_recv','wr_ft_auth_pending_enqueue_for_recv'))
start=prepared.index('BOOLEAN MlmeEnqueueForRecv(');wrapper=prepared[start:prepared.index('\n}',start)+2]
prefix=fixture['prefix'].replace('#define SUBTYPE_ACTION 13','#define SUBTYPE_ACTION 13\n#define SUBTYPE_AUTH 11')+'\n#include <stdlib.h>\n'
actors=fixture['actors'].replace('wr_ft_mlme_enqueue_for_recv','wr_ft_auth_mlme_enqueue_for_recv').replace('wr_ft_pending_enqueue_for_recv','wr_ft_auth_pending_enqueue_for_recv').replace('wr_ft_native_mlme_enqueue_for_recv','wr_ft_auth_native_mlme_enqueue_for_recv')
main=r'''
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
#define RX(n,p) MlmeEnqueueForRecv(&ad,0,&rssi,0,0,n,p,OPMODE_AP)
#else
#define RX(n,p) MlmeEnqueueForRecv(&ad,0,&rssi,n,p,OPMODE_AP)
#endif
int main(void){
 RTMP_ADAPTER ad={0};struct raw_rssi_info rssi={0};UCHAR msg[128]={0};
 FRAME_802_11 *f=(FRAME_802_11 *)msg;
 ad.OpMode=OPMODE_AP;ad.ApCfg.BssidNum=2;ad.ApCfg.MBSSID[1].wdev.bssid[0]=2;
 f->Hdr.FC.Type=FC_TYPE_MGMT;f->Hdr.FC.SubType=SUBTYPE_AUTH;
 f->Hdr.Addr1[0]=2;f->Hdr.Addr2[0]=42;msg[24]=2;msg[26]=1;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[3];
 e->used=e->client=1;e->Sst=SST_ASSOC;e->wcid=3;e->assoc_gen=9;
 e->func_tb_idx=1;e->wdev=&ad.ApCfg.MBSSID[1].wdev;e->Addr[0]=42;
 assert(RX(30,msg));assert(active_calls==1&&!pending_calls&&!native_calls&&active_wcid==3&&active_bss==1);
 ad.MacTab.Content[4]=*e;
 assert(!RX(30,msg));assert(active_calls==1&&!ad.MacTabLock);
 memset(&ad.MacTab.Content[4],0,sizeof(*e));
 for(unsigned n=25;n<30;n++){
  UCHAR *short_msg=malloc(n);assert(short_msg);memcpy(short_msg,msg,n);
  assert(!RX(n,short_msg));free(short_msg);
 }
 e->used=e->client=0;
 assert(RX(30,msg));assert(pending_calls==1&&pending_bss==1&&!pending_wcid);
 ad.wr_ft_pending.live=0;pending_ok=0;
 assert(!RX(30,msg));assert(pending_calls==2&&!ad.wr_ft_pending.live&&!ad.MacTabLock);
 msg[26]=3;assert(RX(30,msg));assert(native_calls==1);
 msg[26]=1;msg[24]=0;assert(RX(30,msg));assert(native_calls==2);
 msg[24]=2;msg[28]=1;assert(!RX(30,msg));assert(native_calls==2);
 puts("PASS | FT AUTH RX | exact active stamp, duplicate refusal, short AUTH refusal, first-peer ticket, failed enqueue release and non-request fallback");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-auth-rx-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(prefix+actors+wrapper+main)
 for flags in ([],['-DCUSTOMER_DCC_FEATURE'],['-DNEIGHBORING_AP_STAT']):
  subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
