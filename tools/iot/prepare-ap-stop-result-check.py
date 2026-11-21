#!/usr/bin/env python3
"""Extract 26 APStop call-site branches; surrounding driver operations mocked."""
import argparse
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
ap=(a.candidate/'ap/ap.c').read_text()
header=(a.candidate/'include/ap.h').read_text()
assert 'BOOLEAN APStop(' in header and 'BOOLEAN APStopBssOnly(' in header
assert 'VOID APStop(' not in header and 'VOID APStopBssOnly(' not in header
cfg=(a.candidate/'ap/ap_cfg.c').read_text()
ufd_start=cfg.index('case RT_OID_WSC_READ_UFD_FILE:')
ufd_end=cfg.index('case RT_OID_WSC_WRITE_UFD_FILE:',ufd_start)
ufd=cfg[ufd_start:ufd_end]
assert ufd.index('if (APStop(pAd)) APStartUp(pAd);')<ufd.index('os_free_mem(NULL, pWscUfdFileName);')
assert 'else Status = -EBUSY;' in ufd
queue=(a.candidate/'common/rtmp_init.c').read_text()
qstart=queue.index('case CMDTHREAD_CHAN_RESCAN:')
qend=queue.index('wr_iot_queue_cleanup(cmdqelmt);',qstart)
assert 'if (!APStop(pAd)) break;' in queue[qstart:qend]
assert 'os_free_mem(pAd, cmdqelmt);' in queue[qend:]
functions=[];tests=[]
for name,call in [('APStop','MacTableReset(pAd, 1)'),('APStopBssOnly','MacTableResetWdev(pAd, wdev_bss)')]:
 start=ap.index('BOOLEAN '+name+'(');end=ap.index('\n}',start)+2;body=ap[start:end]
 guard='if (!'+call+') return FALSE;'
 assert body.count(guard)==1 and body.rstrip().endswith('return TRUE;\n}')
 # This extracts the actual reset refusal checkpoint, not the full AP stop.
 functions.append('static int reset_checkpoint_'+name+'(void){int pAd=0,wdev_bss=0;(void)wdev_bss;'+guard+'actions++;return TRUE;}')
 tests.append('stop_ok=0;actions=0;assert(!reset_checkpoint_'+name+'()&&!actions);stop_ok=1;assert(reset_checkpoint_'+name+'()&&actions==1);')
positive=r'if \(APStop\(pAd\)\) APStartUp\(pAd\);\s*else Status = -EBUSY;'
negative=r'if \(!APStop\(pAd\)\) (?:\{[^{}]*\}|return(?: [^;]+)?;|break;)'
call_count=0;coverage={}
for f in sorted(a.candidate.rglob('*.c')):
 text=f.read_text(errors='replace')
 matches=list(re.finditer(positive+'|'+negative,text))
 if not matches:continue
 coverage[f.relative_to(a.candidate).as_posix()]=len(matches)
 for m in matches:
  branch=m.group();index=call_count;call_count+=1
  # Void call-site refusal becomes a distinct sentinel in this int fixture;
  # this does not change or compile the original parent function signature.
  branch=branch.replace('return;','return -9;')
  is_cleanup='break;' in branch or 'else Status' in branch
  is_positive='else Status' in branch
  if 'NDIS_STATUS_FAILURE' in branch:failure='NDIS_STATUS_FAILURE'
  elif 'return FALSE;' in branch:failure='FALSE'
  elif 'return -1;' in branch:failure='-1'
  elif 'return -9;' in branch:failure='-9'
  elif 'Status = -EBUSY;' in branch:failure='-EBUSY'
  else:failure='0'
  init='int pAd=0,Status=0;(void)Status;'
  if is_positive:body=branch+'\ncleanup++;\nreturn Status;'
  elif is_cleanup:body='switch(1){case 1:'+branch+'APStartUp(pAd);break;}cleanup++;return Status;'
  else:body=branch+'actions++;return 42;'
  functions.append('static int caller_'+str(index)+'(void){'+init+body+'}')
  tests.append('stop_ok=0;starts=actions=cleanup=0;assert(caller_'+str(index)+'()=='+failure+');assert(!starts&&!actions&&cleanup=='+str(int(is_cleanup))+');')
  success='0' if is_cleanup else '42'
  tests.append('stop_ok=1;starts=actions=cleanup=0;assert(caller_'+str(index)+'()=='+success+');assert('+('starts==1&&cleanup==1' if is_cleanup else 'actions==1')+');')
assert call_count==26,(call_count,coverage)
prefix=r'''
#include <assert.h>
#define TRUE 1
#define FALSE 0
#define EBUSY 16
#define NDIS_STATUS_FAILURE -5
static int stop_ok,actions,starts,cleanup;
static int APStop(int pAd){(void)pAd;return stop_ok;}
static int MacTableReset(int pAd,int first){(void)pAd;(void)first;return stop_ok;}
static int MacTableResetWdev(int pAd,int wdev){(void)pAd;(void)wdev;return stop_ok;}
static void APStartUp(int pAd){(void)pAd;starts++;}
'''
a.output.write_text(prefix+'\n'.join(functions)+'\nint main(void){\n'+'\n'.join(tests)+'\nreturn 0;}\n',encoding='utf-8')
print('Extracted 26 call-site branches + two reset checkpoints; enclosing side effects/lifetime unproved')
