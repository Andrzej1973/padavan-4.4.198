#!/usr/bin/env python3
from pathlib import Path
import importlib.util,subprocess,tempfile
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stop_executor',here/'physical-stop-executor.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
source=(here/'peer-close-executor.inc').read_text()
# Reconstruct the reviewed initializer snippets from actual producer literals.
import ast
producer=ast.parse((here/'prepare-radio-adapter-candidate.py').read_text())
fresh=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='init' for t in n.targets))
existing='wr_iot_peer_close_executor_init(&pAd->wr_iot_peer_close_executor);'
fresh=fresh.replace('wr_iot_radio_transition_init(&pAd->wr_iot_transition);',existing+'\n\t\twr_iot_radio_transition_init(&pAd->wr_iot_transition);')
header='#include "peer-close-executor.h"\nstruct wr_iot_peer_close_executor wr_iot_peer_close_executor;'
installed_header,installed_init=module.compose_adapter(header,fresh)
assert installed_header.count('struct wr_iot_physical_stop_record wr_iot_physical_stop;')==1
assert installed_init.count('NdisZeroMemory(&pAd->wr_iot_physical_stop,')==1
assert installed_init.count('NdisZeroMemory(&pAd->wr_iot_physical_lifetime,')==1
assert installed_header.count('struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;')==1
try:module.compose_adapter(installed_header,installed_init)
except ValueError:pass
else:raise AssertionError('duplicate adapter storage accepted')
try:module.compose_adapter(header,fresh.replace(existing,'')+existing)
except ValueError:pass
else:raise AssertionError('reopen/out-of-order initializer accepted')

transformed=module.compose(source)
# Extract the actual installed dispatch preamble; downstream dispatch policy
# remains outside this focused lifetime/exclusion fixture.
opened=module.compose_open_dispatch((here/'peer-open-dispatch.inc').read_text())
try:module.compose_open_dispatch(opened)
except ValueError:pass
else:raise AssertionError('duplicate open gate accepted')
start=opened.index(' NdisAcquireSpinLock(&pAd->MacTabLock);')
end=opened.index(' switch(request->action)',start)
open_gate=opened[start:end]

try:module.compose(transformed)
except ValueError:pass
else:raise AssertionError('duplicate transform accepted')
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include "physical-stop-record.h"
#include "radio-transition.h"
#define INT int
#define VOID void
#define NDIS_STATUS_FAILURE (-1)
#define NDIS_STATUS_SUCCESS 0
#define WR_PEER_CLOSE_CHECKED 2
static int locked,calls,result,task,foreign;
static const void *current=&task;
typedef struct {
 int MacTabLock;
 struct wr_iot_radio_transition wr_iot_transition;
 void *net_dev;
 struct wr_iot_physical_stop_record wr_iot_physical_stop;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 unsigned wr_iot_peer_legacy_close_state;
} RTMP_ADAPTER;
#define NdisAcquireSpinLock(p) ((void)(p),assert(!locked),locked=1)
#define NdisReleaseSpinLock(p) ((void)(p),assert(locked),locked=0)
static int wr_iot_legacy_close_body(void *raw,void *dev){
 RTMP_ADAPTER *ad=raw;assert(!locked&&dev==ad->net_dev);calls++;
 ad->wr_iot_peer_legacy_close_state=result?1:2;
 if(!result){unsigned long s=wr_iot_peer_table_begin(&ad->wr_iot_peer_table_owner);assert(s&&wr_iot_peer_table_close_seal(&ad->wr_iot_peer_table_owner,s));}
 return result;
}
static unsigned long long wr_iot_physical_stop_completion_epoch(RTMP_ADAPTER *ad){assert(ad&&!locked);return 1;}
static int wr_iot_checked_close_body(void*a,void*b,const struct wr_iot_radio_ticket*t,int*s){(void)a;(void)b;(void)t;(void)s;assert(0);return -1;}
'''
prefix+='\nstatic int actual_open_gate(RTMP_ADAPTER *pAd,void *device){struct {void *device;} value={device},*request=&value;int accepted=0;\n'+open_gate+'\n accepted=1;\ndone:NdisReleaseSpinLock(&pAd->MacTabLock);return accepted;}\n'
body=r'''
int main(void){
 unsigned char nonce[16]={1};int device,other_device;
 for(unsigned scenario=0;scenario<4;scenario++){
  RTMP_ADAPTER ad={.net_dev=&device,.wr_iot_transition={.epoch=1}};calls=locked=0;result=scenario==3?-1:0;current=&task;
  if(scenario)assert(wr_iot_physical_stop_arm(&ad.wr_iot_physical_stop,1,2,3,4,nonce,current,&ad.wr_iot_peer_close_executor));
  assert(actual_open_gate(&ad,&device)==(scenario==0)&&!locked);
  if(scenario){struct wr_iot_radio_ticket t={.serial=1};
   assert(wr_iot_drv_close_checked(&ad,&device,&t)==-1&&!calls&&!locked);}
  if(scenario==2){current=&foreign;assert(RTMPDrvClose(&ad,&device)==-1&&!calls&&!locked);current=&task;
   assert(RTMPDrvClose(&ad,&other_device)==-1&&!calls&&!locked);}
  int status=RTMPDrvClose(&ad,&device);assert(calls==1&&!locked);
  assert(status==(scenario==3?-1:0));
  assert(actual_open_gate(&ad,&device)==(scenario==0)&&!locked);
  if(scenario){assert(ad.wr_iot_physical_stop.phase==(scenario==3?WR_PHYS_STOP_FAILED:WR_PHYS_STOP_COMPLETE));
   assert(RTMPDrvClose(&ad,&device)==-1&&calls==1&&!locked);
   struct wr_iot_radio_ticket t={.serial=1};
   assert(wr_iot_drv_close_checked(&ad,&device,&t)==-1&&calls==1&&!locked);}
 }
 RTMP_ADAPTER busy={.net_dev=&device};unsigned char id[16]={1};
 assert(wr_iot_peer_close_executor_enter(&busy.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,1));
 assert(!wr_iot_physical_stop_arm(&busy.wr_iot_physical_stop,1,2,3,4,id,&task,&busy.wr_iot_peer_close_executor));
 assert(busy.wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE);
 assert(wr_iot_peer_close_executor_leave(&busy.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,1,0,1));
 assert(!wr_iot_physical_stop_arm(&busy.wr_iot_physical_stop,1,2,3,4,id,&task,&busy.wr_iot_peer_close_executor));
 puts("PASS actual transformed close executor: unarmed legacy retained, exact task/main-device gate, unlocked body once, real executor/table finish, failure retained and duplicate blocked; arm API/lifetime pins unbound");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-stop-executor-') as d:
    unit=Path(d)/'check.c';unit.write_text(prefix+transformed+body);binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
