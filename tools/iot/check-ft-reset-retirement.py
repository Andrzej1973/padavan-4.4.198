#!/usr/bin/env python3
"""Execute FT retirement inside actual prepared reset reservation fragment."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'ft-iapp-delete-composition.py'))['compose_reset']
base={'include/rtmp.h':'struct wr_ft_iapp_request_state wr_ft_iapp_requests;',
 'include/wr-iot-peer-table-reset-owner.inc':(here/'peer-table-reset-owner.inc').read_text()}
prepared=compose(base,a.source,here)
for invalid in ({},prepared):
 try:compose(invalid,a.source,here)
 except ValueError:pass
 else:raise AssertionError('missing prerequisite or duplicate accepted')
prefix=(here/'check-ft-iapp-detached-admission.c').read_text().split('int main(void)')[0]
prefix=prefix.replace('#include "peer-close-executor.h"',
 '#include "peer-close-executor.h"\n#include "ft-iapp-request-state.h"\ntypedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} STA_TR_ENTRY;',1)
prefix=prefix.replace(' int MacTabLock;',
 ' struct wr_ft_iapp_request_state wr_ft_iapp_requests;int MacTabLock;')
prefix=prefix.replace('MAC_TABLE_ENTRY Content[8];','MAC_TABLE_ENTRY Content[8];STA_TR_ENTRY tr_entry[8];')
prefix+='''
#define DOT11R_FT_SUPPORT 1
#define MAX_LEN_OF_TR_TABLE 8
typedef unsigned int UINT;
typedef int BOOLEAN;
'''
main=r'''
int main(void){
 for(unsigned scenario=0;scenario<5;scenario++){
  RTMP_ADAPTER ad;unsigned char wire[7];struct wr_ft_iapp_token_handle response={0};
  setup(&ad,&ad.wr_ft_iapp_requests,SST_NOT_AUTH,wire);
  struct wr_ft_iapp_request_state *state=&ad.wr_ft_iapp_requests,saved;
  struct wifi_dev *scope=scenario==3?&ad.ApCfg.MBSSID[2].wdev:NULL;
  if(scenario==1)assert(wr_ft_iapp_token_claim_locked(&state->ledger,wire,
   ad.MacTab.Content[7].Addr,ad.ApCfg.MBSSID[2].wdev.bssid,&response));
  if(scenario==2)ad.wr_assoc_event_users[7]=1;
  if(scenario==4){ad.MacTab.tr_entry[7].wr_iot_setup_observed=1;ad.MacTab.tr_entry[7].wr_iot_setup_result=-1;}
  saved=*state;
  unsigned long serial=wr_iot_peer_reset_begin(&ad,scope);
  assert(!ad.MacTabLock);
  if(scenario==0){
   assert(serial&&ad.wr_iot_peer_table_owner.active);
   assert(!state->request_by_wcid[7].serial&&!state->preauth[7].serial);
   assert(state->ledger.next_serial==saved.ledger.next_serial);
   assert(wr_iot_peer_reset_finish(&ad,serial,1));
  }else if(scenario==3){
   assert(serial&&!memcmp(state,&saved,sizeof(saved)));
   assert(wr_iot_peer_reset_finish(&ad,serial,1));
  }else{
   assert(!serial&&!ad.wr_iot_peer_table_owner.active&&!ad.wr_iot_peer_table_owner.poisoned);
   assert(!memcmp(state,&saved,sizeof(saved)));
  }
 }
 puts("PASS | native reset reservation FT retirement | full reset retires before unlock; CLAIMED/busy preflight rolls back reservation atomically; scoped reset preserves registry for per-entry deletion; native failed-setup gate retained");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-reset-owner-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check'
 c.write_text(prefix+prepared['include/wr-iot-peer-table-reset-owner.inc']+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
