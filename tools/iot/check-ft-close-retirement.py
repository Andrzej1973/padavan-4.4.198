#!/usr/bin/env python3
"""Execute actual close hold/clear/seal fragment with FT retirement."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-reset-retirement.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
compose=runpy.run_path(str(here/'ft-iapp-delete-composition.py'))['compose_close']
base={'include/rtmp.h':'struct wr_ft_iapp_request_state wr_ft_iapp_requests;',
 'include/wr-iot-peer-close-table.inc':(here/'peer-close-table.inc').read_text()}
prepared=compose(base,a.source,here)
for invalid in ({},prepared):
 try:compose(invalid,a.source,here)
 except ValueError:pass
 else:raise AssertionError('missing prerequisite or duplicate accepted')
prefix=data['prefix'].replace('int MacTabLock;', 'unsigned long wr_iot_peer_close_serial;int MacTabLock;')
prefix=prefix.replace('MAC_TABLE_ENTRY Content[8];','unsigned int Size;MAC_TABLE_ENTRY Content[8];')
prefix+='''
#define FALSE 0
#define TRUE 1
#define NdisZeroMemory(p,n) memset(p,0,n)
typedef __typeof__(((RTMP_ADAPTER *)0)->MacTab) MAC_TABLE;
'''
main=r'''
int main(void){
 for(unsigned scenario=0;scenario<3;scenario++){
  RTMP_ADAPTER ad;unsigned char wire[7],mac[6]={42},bssid[6]={2};
  struct wr_ft_iapp_token_handle claim={0};
  setup(&ad,&ad.wr_ft_iapp_requests,SST_NOT_AUTH,wire);
  memset(&ad.MacTab,0,sizeof(ad.MacTab));
  if(scenario==1)assert(wr_ft_iapp_token_claim_locked(&ad.wr_ft_iapp_requests.ledger,wire,mac,bssid,&claim));
  assert(wr_iot_peer_close_hold(&ad));
  unsigned long serial=ad.wr_iot_peer_close_serial;
  ad.MacTab.Size=99; /* marker proves refused clear does not erase table */
  if(scenario==2)ad.wr_assoc_event_users[7]=1;
  if(scenario){
   struct wr_ft_iapp_request_state saved=ad.wr_ft_iapp_requests;
   assert(!wr_iot_peer_close_clear(&ad));
   assert(ad.MacTab.Size==99&&ad.wr_iot_peer_close_serial==serial);
   assert(ad.wr_iot_peer_table_owner.active&&!ad.MacTabLock);
   assert(!memcmp(&saved,&ad.wr_ft_iapp_requests,sizeof(saved)));
  }else{
   assert(wr_iot_peer_close_clear(&ad));
   assert(!ad.MacTab.Size&&!ad.wr_ft_iapp_requests.current[7].serial&&!ad.wr_ft_iapp_requests.preauth[7].serial);
   assert(ad.wr_ft_iapp_requests.token_seeded&&ad.wr_ft_iapp_requests.ledger.next_serial==1);
   assert(wr_iot_peer_close_finish(&ad)&&ad.wr_iot_peer_table_owner.closed);
  }
 }
 puts("PASS | native close FT retirement | retire before MacTab clear; CLAIMED/busy preserve table, registry and close reservation; success preserves token history and seals close");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-close-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text(prefix+prepared['include/wr-iot-peer-close-table.inc']+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
