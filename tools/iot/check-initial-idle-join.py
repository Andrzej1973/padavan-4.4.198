#!/usr/bin/env python3
"""Execute actual composed reaper with real receipt helpers and injected kernel refs."""
from pathlib import Path
import ast,runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
helpers=runpy.run_path(str(here/'close-owner-composition.py'))
compose=helpers['compose_recovery_return']
tree=ast.parse((here/'prepare-mbss-reaper-gate.py').read_text())
body=(here/'mbss-recovery-join.inc').read_text()
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='one' and len(node.args)==3:
  if isinstance(node.args[1],ast.Constant) and isinstance(node.args[1].value,str) and node.args[1].value in ['INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad)',' ready=wr_iot_mbss_recovery_idle_locked(ad);']:
   old,new=ast.literal_eval(node.args[1]),ast.literal_eval(node.args[2]);assert body.count(old)==1;body=body.replace(old,new)
wrappers=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='wrapper' for t in n.targets)]
assert len(wrappers)==1
body=compose(helpers['compose_recovery_join'](body+wrappers[0]))
idle=runpy.run_path(str(here/'initial-idle-lifetime-composition.py'))
work=helpers['compose_recovery_idle']((here/'mbss-recovery-work.inc').read_text())
_,body=idle['retirement'](work,body)
base=(here/'check-driver-api-close-join.c').read_text()
setup=base[base.index('  int dev;'):base.index('  switch(fault)')].replace('int dev;', 'struct device dev={0};')
code='''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-join.h"
#include "mbss-reaper-gate.h"
#include "mbss-recovery-storage.h"
#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define WDEV_NUM_MAX 0
#define NULL ((void *)0)
typedef int INT;typedef unsigned int UINT;typedef unsigned long ULONG;
struct device {int refs;};typedef struct device *PNET_DEV;
struct work_struct {int busy;};
typedef struct {
 int wr_iot_transition_lock;
 struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct {int active;} wr_iot_idle_probe;
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[1];
 struct wr_iot_interface_ref wr_iot_interface_refs[1];
 struct {struct work_struct work;}wr_iot_mbss_work[1];
} RTMP_ADAPTER;
static int held,puts,expect_api;static RTMP_ADAPTER *current_ad;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int wr_iot_os_join_context(void){return 0;}
static int work_busy(struct work_struct *w){assert(held);return w->busy;}
static void flush_work(struct work_struct *w){assert(w&&!held);}
static void dev_put(PNET_DEV dev){
 assert(!held&&dev->refs==1&&current_ad->wr_iot_mbss_reaper_gate.reaping);puts++;dev->refs--;
 if(expect_api)assert(current_ad->wr_iot_close_owner.recovery_join_pending&&!current_ad->wr_iot_close_owner.recovery_netdev_returned);
}
'''+body+'''
int main(void){
 for(unsigned fault=0;fault<6;fault++){
'''+setup+'''
  (void)receipt;(void)joined;
  RTMP_ADAPTER ad={0};ad.wr_iot_close_owner=close;
  ad.wr_iot_mbss_recovery[0]=recovery;ad.wr_iot_interface_refs[0]=record;
  dev.refs=1;held=puts=0;current_ad=&ad;expect_api=fault!=3&&fault!=5;
  if(fault==1)ad.wr_iot_close_owner.generation++;
  if(fault==2)ad.wr_iot_mbss_recovery[0].completed=0;
  if(fault==3||fault==5)ad.wr_iot_close_owner.active=0;
  if(fault==5)ad.wr_iot_idle_probe.active=1;
  if(fault==4)ad.wr_iot_mbss_reaper_gate.reaping=1;
  struct wr_iot_mbss_recovery_owner recovery_before=ad.wr_iot_mbss_recovery[0];
  struct wr_iot_driver_close_owner api_before=ad.wr_iot_close_owner;
  int result=wr_iot_mbss_recovery_join_completed(&ad);
  assert(!held&&ad.wr_iot_mbss_reaper_gate.reaping==(fault==4)&&result==(fault==3?0:-1));
  if(fault==0){
   assert(puts==1&&dev.refs==0&&ad.wr_iot_close_owner.recovery_netdev_returned);
   assert(!ad.wr_iot_close_owner.recovery_join_pending&&ad.wr_iot_close_owner.module_held);
   assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&puts==1);
  }else if(fault==3||fault==5){
   assert(puts==1&&dev.refs==0);
   if(fault==5){assert(ad.wr_iot_idle_probe.active);assert(wr_iot_mbss_recovery_join_completed(&ad)==-1&&puts==1);}
  }
  else {
   assert(!puts&&dev.refs==1&&!ad.wr_iot_close_owner.recovery_netdev_returned);
   assert(!memcmp(&recovery_before,&ad.wr_iot_mbss_recovery[0],sizeof(recovery_before)));
   assert(!memcmp(&api_before,&ad.wr_iot_close_owner,sizeof(api_before)));
  }
 }
 puts("PASS actual reaper with idle-probe fence: active probe refuses retirement, native dev_put owner retained; receipt pending during dev_put, confirmed afterward; drift/incomplete retain; duplicate no second put, legacy release retained");
 return 0;
}
'''
# Avoid fixture's counter shadowing libc puts.
code=code.replace('held,puts,','held,put_calls,').replace('puts++;','put_calls++;').replace('held=puts=0','held=put_calls=0').replace('puts==','put_calls==').replace('!puts&&','!put_calls&&')
with tempfile.TemporaryDirectory(prefix='wr-idle-join-binding-') as tmp:
 src=Path(tmp)/'test.c';out=Path(tmp)/'test';src.write_text(code)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(here),str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
try:compose(body)
except ValueError:pass
else:raise AssertionError('Duplicate composition accepted')
