#!/usr/bin/env python3
"""Execute the actual transformed begin-close with sentinel handoff injection."""
import ast,runpy,subprocess,tempfile
from pathlib import Path
here=Path(__file__).parent
compose=runpy.run_path(str(here/'close-owner-composition.py'))['compose']
original=(here/'mbss-close-checked.inc').read_text()
text=compose(original)
start=text.index('INT wr_iot_mbss_begin_close(');end=text.index('/* Caller holds the common adapter lock.',start)
body=text[start:end]
tree=ast.parse((here/'prepare-mbss-checked-stop-candidate.py').read_text())
callbacks=[n.value.value.decode() for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REPLACEMENT' for t in n.targets) and isinstance(n.value,ast.Constant)]
assert len(callbacks)==1
callback=callbacks[0]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include "interface-registry.h"
#include "radio-transition.h"
typedef int INT;typedef unsigned long ULONG;
typedef const void *PNET_DEV;
typedef struct {const void *net_dev;int wr_iot_transition_lock;struct wr_iot_interface_ref wr_iot_interface_refs[2];struct wr_iot_radio_transition wr_iot_transition;} adapter,*PRTMP_ADAPTER;
static adapter test_adapter;static int handoff,legacy_locks,handoffs;
#define WDEV_NUM_MAX 1
#define RTMP_OS_NETDEV_GET_PRIV(dev) (&test_adapter)
#define VIRTUAL_IF_NUM(ad) 2
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);flags=1;legacy_locks++;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);assert(flags);}while(0)
static int wr_iot_driver_close_take_bound(adapter *a,PNET_DEV d,struct wr_iot_radio_ticket *t,unsigned long *g){assert(a&&d&&t&&g);handoffs++;if(!handoff){t->serial=77;*g=2;}return handoff;}
'''
executor=r'''
static int executor_calls,executor_status;
INT wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long generation,const struct wr_iot_radio_ticket *ticket){assert(dev&&generation==2&&ticket->serial==77);executor_calls++;return executor_status;}
'''
post=r'''
int main(void){
 int dev,main_dev;unsigned long sequence=0,generation;struct wr_iot_radio_ticket ticket;
 for(int result=-1;result<=1;result++){
  test_adapter=(adapter){0};wr_iot_radio_transition_init(&test_adapter.wr_iot_transition);test_adapter.wr_iot_transition.phase=WR_RADIO_READY;test_adapter.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(test_adapter.wr_iot_interface_refs,2,&sequence,&dev,WR_REF_FAMILY_MBSS);
  assert(r);r->published=1;r->phase=WR_REF_OWNED;r->last_token=2;
  struct wr_iot_interface_ref *main_ref=wr_iot_registry_add_family(test_adapter.wr_iot_interface_refs,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  assert(main_ref);main_ref->published=1;main_ref->phase=WR_REF_OWNED;main_ref->last_token=1;
  legacy_locks=handoffs=0;handoff=result;
  assert(wr_iot_mbss_begin_close(&dev,&ticket,&generation)==(result<0?-1:0));
  assert(handoffs==1&&legacy_locks==(result==1));
  if(!result)assert(ticket.serial==77&&generation==2&&!test_adapter.wr_iot_transition.busy);
  if(result<0)assert(!test_adapter.wr_iot_transition.busy&&!generation);
  if(result==1)assert(test_adapter.wr_iot_transition.busy==WR_RADIO_BSS_CLOSE);
 }
 handoff=0;legacy_locks=handoffs=executor_calls=0;
 for(int fail=-1;fail<=0;fail++){executor_status=fail;assert(MBSS_VirtualIF_Close(&dev)==fail);}
 assert(executor_calls==2&&handoffs==2&&!legacy_locks);
 handoff=-1;assert(MBSS_VirtualIF_Close(&dev)==-1&&executor_calls==2);
 puts("PASS actual transformed begin_close and MBSS callback: same-ticket executor dispatch, checked failure propagated, refusal never executes; legacy path retained");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-close-composition-') as d:
 src=Path(d)/'check.c';exe=Path(d)/'check';src.write_text(prefix+body+executor+callback+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
try:compose(text)
except ValueError:pass
else:raise AssertionError('Double composition accepted')
