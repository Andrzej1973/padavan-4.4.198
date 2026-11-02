#!/usr/bin/env python3
"""Release RTNL before pinned recovery worker's physical close continuation.

Ordinary synchronous ndo_stop/failed-VERIFY paths still require conversion.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
m=json.loads(src.with_name(src.name+'.manifest.json').read_text());actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=m['merged_driver_sha256'] or m.get('production_installed') is not False or 'main_reopen_fence_layer' not in m:p.error('changed/unsupported merged input')
name='os/linux/rt_main_dev.c';s=(src/name).read_text();start=s.index('static int wr_iot_main_recovery_execute(');end=s.index('\n}',start)+2;original=s[start:end];body=original
old='static int wr_iot_main_recovery_execute(PRTMP_ADAPTER adapter)';new='static int wr_iot_main_recovery_execute(PRTMP_ADAPTER adapter, int *rtnl_released)';assert body.count(old)==1;body=body.replace(old,new,1)
old=' if (!adapter) return -1;';new=' if (!adapter || !rtnl_released) return -1;\n *rtnl_released=0;';assert body.count(old)==1;body=body.replace(old,new,1)
anchor=' if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,'
prefix=''' /* RTNL protected admission/preclose. Exact owner pins adapter/netdev;
  * root reopen stays fenced through external callback join and reap. */
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 bound = owner->phase == WR_MAIN_OWNER_RUNNING && owner->deferred_owners &&
  owner->device == net_dev && owner->generation == generation &&
  owner->open_token == token && owner->close_ticket_valid &&
  owner->close_ticket.serial == ticket.serial &&
  wr_iot_main_recovery_action(owner, record, &adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs, WDEV_NUM_MAX + 1,
   VIRTUAL_IF_NUM(adapter)) == WR_MAIN_RECOVERY_CONTINUE_CLOSE;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (!bound) goto retain;
 rtnl_unlock();
 *rtnl_released=1;
'''
assert body.count(anchor)==1;body=body.replace(anchor,prefix+anchor,1)
changed=s[:start]+body+s[end:]
old=' (void)wr_iot_main_recovery_execute(adapter);\n rtnl_unlock();';new=''' {
  int rtnl_released=0;
  (void)wr_iot_main_recovery_execute(adapter, &rtnl_released);
  if (!rtnl_released) rtnl_unlock();
 }'''
assert changed.count(old)==1;changed=changed.replace(old,new,1)
# Full body changes are exact and independent of other main/open code.
restored=changed.replace(new,old,1).replace(body,original,1);assert restored==s
shutil.copytree(src,out);(out/name).write_text(changed);digest=hashlib.sha256((out/name).read_bytes()).hexdigest();m['merged_driver_sha256'][name]=digest;m['candidate_driver_sha256'][name]=digest
m.update(production_installed=False,target_compiled=False,runtime_verified=False)
m['main_recovery_rtnl_split_layer']={'target_compiled':False,'runtime_verified':False,'ordinary_close_converted':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Staged pinned recovery continuation outside RTNL; ordinary close paths remain open')
