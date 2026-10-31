#!/usr/bin/env python3
"""Allow the exact removing auxiliary owner to close; fence other removals."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
name='include/aux-close-claim.h';raw=(src/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='57738ffb5d63269ba09d9c203c9189cdec8db34a061708a61f15e41fb78361c9':p.error('unreviewed close admission predecessor')
s=raw.decode()
anchor='static inline int wr_iot_aux_close_reserve('
helper='''/* Caller holds the adapter lock. Removal fences new opens, but must not
 * prevent that exact still-owned generation from retiring its existing pin.
 * Other removals and duplicate identities remain ambiguous and are refused. */
static inline int wr_iot_aux_close_count_matches(
 const struct wr_iot_interface_ref *slots,unsigned int count,
 const struct wr_iot_interface_ref *target,unsigned int vendor_count){
 unsigned int i,owned=0,seen=0;
 if(!slots||!target||!target->device||!target->generation||!target->published||
    target->phase!=WR_REF_OWNED||target->removal_stage)return 0;
 for(i=0;i<count;i++){
  const struct wr_iot_interface_ref *r=&slots[i];
  if(r==target)seen++;
  else if(r->device==target->device||r->removing)return 0;
  if(r->phase==WR_REF_IDLE)continue;
  if(r->phase!=WR_REF_OWNED||!r->device||!r->generation||
     !r->published||owned==~0U)return 0;
  owned++;
 }
 return seen==1&&owned==vendor_count;
}
'''
if s.count(anchor)!=1:p.error('changed admission anchor')
s=s.replace(anchor,helper+anchor,1)
old='wr_iot_registry_count_matches(slots,count,vendor_count)'
if s.count(old)!=1:p.error('changed count check')
s=s.replace(old,'wr_iot_aux_close_count_matches(slots,count,record,vendor_count)',1)
shutil.copytree(src,out);(out/name).write_text(s,encoding='utf-8',newline='\n')
print('Prepared exact-target removing close admission; no callback/recovery completion claim')
