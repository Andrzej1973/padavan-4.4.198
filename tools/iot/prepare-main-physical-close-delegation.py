#!/usr/bin/env python3
"""Delegate last-user main physical close to the pinned recovery worker."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'main_recovery_rtnl_split_layer' not in m:p.error('changed/unsupported merged input')
name='os/linux/rt_main_dev.c';original=(src/name).read_text();s=original
start=s.index('static int wr_iot_main_verify_recovery_submit(');end=s.index('\n}',start)+2;old_submit=s[start:end];submit=old_submit
old=' int queued = 0, accepted, reaper_accepted = 0;'
new=old+'\n int retirement_owner_active;\n enum wr_iot_main_recovery_queue_origin origin;'
assert submit.count(old)==1;submit=submit.replace(old,new,1)
old=' owner = &adapter->wr_iot_main_recovery;'
new=old+'''
 retirement_owner_active = adapter->wr_iot_transition.retiring &&
  adapter->wr_iot_pci_retirement.phase == WR_PCI_RETIRE_DRAINING;
 origin = retirement_owner_active ? WR_MAIN_QUEUE_RETIREMENT_CLOSE : WR_MAIN_QUEUE_NORMAL;'''
assert submit.count(old)==1;submit=submit.replace(old,new,1)
old='    1, 1, WR_MAIN_QUEUE_NORMAL, 0);';assert submit.count(old)==2
submit=submit.replace(old,'    1, 1, origin, retirement_owner_active);')
# Move the existing submission function ahead of ndo_stop; avoid a second
# declaration that would confuse source-body extractors.
s=s[:start]+s[end:];anchor='int MainVirtualIF_close(IN struct net_device *net_dev)';assert s.count(anchor)==1;s=s.replace(anchor,submit+'\n\n'+anchor,1)
start=s.index(anchor);end=s.index('\n}',start)+2;old_close=s[start:end]
old=' if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,'
new=''' /* Last-user physical joins must run outside ndo_stop's RTNL. The
  * existing module pin and newly acquired netdev hold belong to recovery. */
 if (ticket.operation == WR_RADIO_CLOSE)
  return wr_iot_main_verify_recovery_submit(adapter, net_dev, generation,
                                           &ticket) ? 0 : -1;
'''+old
assert old_close.count(old)==1;new_close=old_close.replace(old,new,1)
old_failure='''                                     &generation, &token, &wait_serial) != 0)
  return -1;'''
new_failure='''                                     &generation, &token, &wait_serial) != 0) {
  struct wr_iot_interface_ref *record;
  ULONG flags;
  generation=0;
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
  record=wr_iot_registry_find_owned(adapter->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,net_dev);
  if (record && record->phase==WR_REF_OWNED) generation=record->generation;
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  if (generation)
   (void)wr_iot_main_verify_recovery_submit(adapter,net_dev,generation,NULL);
  return -1;
 }'''
assert new_close.count(old_failure)==1;new_close=new_close.replace(old_failure,new_failure,1)
old_failure='''                                    &ticket) != 0)
  return -1;'''
new_failure='''                                    &ticket) != 0) {
  (void)wr_iot_main_verify_recovery_submit(adapter,net_dev,generation,&ticket);
  return -1;
 }'''
assert new_close.count(old_failure)==1;new_close=new_close.replace(old_failure,new_failure,1)
s=s[:start]+new_close+s[end:]
old='''      wr_iot_main_close_continue_checked(adapter,net_dev,close_generation,'''
new='''      close_ticket.operation != WR_RADIO_CLOSE &&
'''+old
assert s.count(old)==1;s=s.replace(old,new,1)
# Reverse substitutions and restore the relocated helper at its original offset.
without=s.replace(new,old,1).replace(new_close,old_close,1).replace(submit+'\n\n','',1)
restored=without[:original.index(old_submit)]+old_submit+without[original.index(old_submit):]
assert restored==original
shutil.copytree(src,out);(out/name).write_text(s);digest=hashlib.sha256((out/name).read_bytes()).hexdigest();m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['main_physical_close_delegation_layer']={'target_compiled':False,'runtime_verified':False,'physical_close_delegated':True}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged last-user ndo_stop/VERIFY delegation with PCI drain queue origin')
