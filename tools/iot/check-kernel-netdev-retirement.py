#!/usr/bin/env python3
"""Verify pinned kernel unregister/RTNL reference-drain semantics and driver seam."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('kernel_files',type=Path);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new report output required')
pins={'dev.c':'f6bb16cbf40a0cbbcc00a174156e79ca4f0b66becd91b9354d7b83ef0fabe22a',
 'rtnetlink.c':'9f80fbdd36157a7ad051b21661f57d8136119cfe8c33f08c68da813dc8d4ae9a',
 'netdevice.h':'75e8135ec0148d6d3976c319a693c8511d3916bcc5c2aba52f2ae82b0cb9a259'}
texts={}
for name,digest in pins.items():
 f=a.kernel_files/name
 if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:p.error('unreviewed kernel source: '+name)
 texts[name]=f.read_text()
def function(text,signature):
 start=text.index(signature);opening=text.index('{',start);depth=0
 for end in range(opening,len(text)):
  if text[end]=='{':depth+=1
  elif text[end]=='}':
   depth-=1
   if not depth:return text[start:end+1]
 raise ValueError('unterminated '+signature)
unlock=function(texts['rtnetlink.c'],'void rtnl_unlock(void)')
assert 'netdev_run_todo();' in unlock
todo=function(texts['dev.c'],'void netdev_run_todo(void)')
ordered=['__rtnl_unlock();','rcu_barrier();','dev->reg_state = NETREG_UNREGISTERED;',
         'netdev_wait_allrefs(dev);','dev->destructor(dev);']
positions=[todo.index(x) for x in ordered];assert positions==sorted(positions)
wait=function(texts['dev.c'],'static void netdev_wait_allrefs(')
assert 'while (refcnt != 0)' in wait and 'refcnt = netdev_refcnt_read(dev);' in wait
assert 'msleep(250);' in wait
queue=function(texts['dev.c'],'void unregister_netdevice_queue(')
assert queue.index('rollback_registered(dev);')<queue.index('net_set_todo(dev);')
driver=a.candidate/'os/linux/rt_linux.c';s=driver.read_text()
protect=function(s,'void RtmpOSNetDevProtect(')
assert 'rtnl_lock();' in protect and 'rtnl_unlock();' in protect
detach=function(s,'void RtmpOSNetDevDetach(');assert 'unregister_netdevice(pNetDev);' in detach
wds=a.candidate/'ap/ap_wds.c';ws=wds.read_text();remove=function(ws,'INT WDS_Remove(')
order=['RtmpOSNetDevDetach(wdev->if_dev);','RtmpOSNetDevProtect(0);','wr_iot_registry_after_unregister(']
detach_pos=remove.index(order[0])
unlock_pos=remove.index(order[1],detach_pos)
receipt_pos=remove.index(order[2])
assert detach_pos<unlock_pos<receipt_pos
report={'passed':True,'scope':'exact pinned source/control-order evidence, not kernel runtime',
 'kernel_sha256':pins,'driver_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [driver,wds]},
 'facts':['rtnl_unlock invokes netdev_run_todo before returning',
  'todo drains RCU callbacks and waits accounted netdev refs before completing',
  'NETREG_UNREGISTERED is set BEFORE wait_allrefs; state alone is insufficient',
  'driver WDS receipt follows detach plus RTNL unlock return',
  'wait_allrefs can wait indefinitely while refs remain'],
 'kernel_accounted_ref_receipt_supported_at_this_seam':True,
 'vendor_callbacks_quiescent':False,'dma_quiescent':False,
 'target_compiled':False,'runtime_verified':False,'adapter_release_accepted':False}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASS pinned kernel/driver RTNL seam; vendor raw references and DMA remain unproved')
