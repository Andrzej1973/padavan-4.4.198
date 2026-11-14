"""Actual internal binding and actual CLOSED observer, registers/rings injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
base=(here/'check-mt7603-closed-binding.c').read_text()
prefix=base[:base.index('static int rtnl=1;')]
prefix='#include "physical-rebind-probe.h"\n'+prefix
prefix=prefix.replace(' struct wr_iot_driver_owner wr_iot_driver_owner;', ''' struct wr_iot_driver_owner wr_iot_driver_owner;
 struct {int active;} wr_iot_close_owner,wr_iot_physical_lifetime;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;
 struct wr_iot_physical_rebind_probe wr_iot_physical_rebind_probe;''')
prefix=prefix.replace('assert(!*(lock));*(lock)=1;','assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock);*(lock)=1;')
code=prefix+r'''
typedef struct adapter RTMP_ADAPTER;
struct pid {int id;};static struct pid identity,foreign;
#define current ((void *)1)
static struct pid *task_pid(void *task){assert(task==current);return &identity;}
static int fault,reads;
static int rtnl_is_locked(void){return fault!=1;}
static int netif_running(PNET_DEV dev){return dev->running;}
static void read_reg(PRTMP_ADAPTER ad,unsigned address,unsigned *out){
 assert(ad->BcnRingLock&&!ad->wr_iot_transition_lock);reads++;
 *out=address==ARB_BCNQCR0?1:0;if(fault==3)*out=0xffffffffU;
}
#define RTMP_IO_READ32 read_reg
static int WrBeaconDmaOutstanding(PRTMP_ADAPTER ad,unsigned id)
{assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&id==2);return fault==4?1:0;}
static int WrBeaconTxSOutstanding(PRTMP_ADAPTER ad,unsigned id){
 assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&id==2);
 if(fault==5)ad->wr_iot_transition.epoch++;
 if(fault==6)ad->wr_iot_transition.serial++;
 if(fault==7)ad->wr_iot_control_users=1;
 if(fault==8)ad->wr_iot_physical_terminal.request.nonce[0]++;
 return 0;
}
#include "mt7603-closed-observe.h"
#include "physical-rebind-binding.inc"
int main(void){
 for(fault=0;fault<10;fault++){
  struct device main_dev={1},iot_dev={0};
  struct adapter storage={.mt7603=1,.flags=3,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  struct adapter *ad=&storage;
  ad->ApCfg.MBSSID[0].wdev.if_dev=&main_dev;ad->ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
  ad->ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
  unsigned long sequence=0;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *i=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  m->published=i->published=1;m->phase=WR_REF_OWNED;m->last_token=4;
  i->last_token=9;i->close_serial=10;i->close_epoch=5;i->close_stage=4;
  struct wr_iot_physical_stop_request request={.action=WR_STOP_RELEASE,.epoch=5,
   .generation=2,.open_token=9,.closed_serial=10,.attempt=12,.nonce={1}};
  ad->wr_iot_physical_terminal.owner=&identity;ad->wr_iot_physical_terminal.request=request;
  ad->wr_iot_physical_terminal.ready=1;ad->wr_iot_physical_terminal.status=WR_STOP_RELEASED;
  ad->wr_iot_physical_terminal.origin=(struct wr_iot_physical_stop_origin){.main_generation=1,
   .main_open_token=3,.arm_epoch=5,.ticket_serial=7,.ticket_epoch=6,.completion_epoch=6,.valid=1};
  ad->wr_iot_main_recovery.last_release=(struct wr_iot_main_recovery_release_receipt){
   .device=&main_dev,.generation=1,.open_token=3,.close_serial=9,
   .ticket={.serial=7,.epoch=6,.operation=WR_RADIO_CLOSE},.completion_epoch=6,.valid=1};
  wr_iot_radio_transition_init(&ad->wr_iot_transition);
  ad->wr_iot_transition.epoch=7;ad->wr_iot_transition.serial=8;ad->wr_iot_transition.retired_serial=8;
  ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;
  if(fault==2)ad->wr_iot_physical_terminal.owner=&foreign;
  if(fault==9)ad->wr_iot_physical_lifetime.active=1;
  reads=0;int result=wr_iot_physical_rebind_observe(ad,&iot_dev,&request);
  assert((result==0)==(fault==0));
  assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&i->close_epoch==5&&main_dev.running);
  if(!fault){
   struct wr_iot_driver_open_request open_request={.adapter_epoch=7,.device_generation=2,.request_id={8}};
   assert(wr_iot_driver_owner_query(&ad->wr_iot_driver_owner,open_request.request_id,7,2));
   ad->wr_iot_control_users=1;
   assert(wr_iot_physical_rebind_request_enter(ad,&iot_dev,&request,&open_request)==-EBUSY);
   assert(!ad->wr_iot_physical_rebind_probe.spent);
   ad->wr_iot_control_users=0;
   assert(!wr_iot_physical_rebind_request_enter(ad,&iot_dev,&request,&open_request));
   assert(ad->wr_iot_physical_rebind_probe.spent&&ad->wr_iot_driver_owner.active);
   assert(wr_iot_physical_rebind_request_enter(ad,&iot_dev,&request,&open_request)==-EBUSY);
   assert(wr_iot_driver_owner_leave(&ad->wr_iot_driver_owner,current,&iot_dev,&ad->wr_iot_transition,ad->wr_iot_interface_refs,3));
   assert(ad->wr_iot_physical_rebind_probe.spent&&!ad->wr_iot_driver_owner.active);
  }
  if(fault==6)assert(result==-EUCLEAN&&ad->wr_iot_physical_rebind_probe.active&&ad->wr_iot_control_poisoned);
  else assert(!ad->wr_iot_physical_rebind_probe.active);
  if(fault==1||fault==2||fault==9)assert(!reads);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rebind-binding-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True,timeout=15)
print('PASS actual rebind binding/observer: RTNL/PID/physical owner gates, MMIO/DMA refusal, epoch/control/nonce drift, foreign ticket retained/poisoned, disjoint locks, history preserved; registers/rings injected')
