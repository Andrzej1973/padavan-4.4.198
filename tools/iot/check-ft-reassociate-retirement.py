#!/usr/bin/env python3
"""Execute composed reassociation helper with pending FT request actors."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)
# Storage schema prerequisite, whose fresh-allocation composer is checked by
# check-ft-auth-request-context.py. Actual runtime state uses real header.
base['include/rtmp.h']+='\nstruct wr_ft_iapp_request_state wr_ft_iapp_requests;\n'
compose=runpy.run_path(str(here/'ft-iapp-delete-composition.py'))['compose_reassociate']
prepared=compose(base,a.source,here)
kernel=prepared['include/assoc-generation-kernel.h']
start=kernel.index('static inline int wr_assoc_reassociate(')
body=kernel[start:kernel.index('\n}',start)+2]
assert body.index('wr_ft_iapp_slot_retire_locked(')<body.index('generation = wr_assoc_generation_next(')
for invalid in ({},prepared):
 try:compose(invalid,a.source,here)
 except ValueError:pass
 else:raise AssertionError('missing prerequisite or duplicate accepted')
prefix=(here/'check-ft-iapp-detached-admission.c').read_text().split('int main(void)')[0]
prefix=prefix.replace(' int MacTabLock;',
 ' struct wr_ft_iapp_request_state wr_ft_iapp_requests;int MacTabLock;')
prefix=prefix.replace('#include "peer-close-executor.h"',
 '#include "peer-close-executor.h"\n#include "ft-iapp-request-state.h"',1)
actors='''
#define DOT11R_FT_SUPPORT 1
static int wr_assoc_try_table_lock(RTMP_ADAPTER *ad){
 if(ad->MacTabLock)return 0;
 ad->MacTabLock=1;return 1;
}
'''
main=r'''
int main(void){
 for(unsigned scenario=0;scenario<6;scenario++){
  RTMP_ADAPTER ad;unsigned char wire[7];struct wr_ft_iapp_token_handle response={0};
  setup(&ad,&ad.wr_ft_iapp_requests,SST_NOT_AUTH,wire);
  /* setup clears adapter before initializing the passed registry. */
  MAC_TABLE_ENTRY *entry=&ad.MacTab.Content[7];
  struct wr_ft_iapp_request_state *state=&ad.wr_ft_iapp_requests,saved;
  if(scenario==1)ad.wr_assoc_event_users[7]=1;
  if(scenario==2)assert(wr_ft_iapp_token_claim_locked(&state->ledger,wire,entry->Addr,entry->wdev->bssid,&response));
  if(scenario==3)state->current[7].serial++;
  if(scenario==4)ad.MacTabLock=1;
  MAC_TABLE_ENTRY foreign=*entry;if(scenario==5)entry=&foreign;
  saved=*state;
  int result=wr_assoc_reassociate(&ad,entry);
  if(scenario){
   assert(!result&&entry->assoc_gen==3&&ad.wr_assoc_generations[7]==3);
   assert(!memcmp(state,&saved,sizeof(saved)));
   assert(ad.MacTabLock==(scenario==4));
  }else{
   assert(result&&entry->assoc_gen==4&&ad.wr_assoc_visible[7]==4);
   assert(!state->current[7].serial&&!state->preauth[7].serial&&!state->detached[7]);
   assert(!wr_ft_iapp_token_claim_locked(&state->ledger,wire,entry->Addr,entry->wdev->bssid,&response));
   assert(!ad.MacTabLock);
  }
 }
 puts("PASS | native reassociation retirement | WAITING/preauth retired before generation; busy event, CLAIMED, stale handle, busy lock and foreign pointer refuse without mutation; old token refused");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-reassoc-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(prefix+actors+body+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
