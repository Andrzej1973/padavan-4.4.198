#!/usr/bin/env python3
"""Actual idle binding and existing hardware observer; injected registers only."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
base=(here/'check-mt7603-closed-binding.c').read_text()
prefix=base[:base.index('static int rtnl=1;')]
prefix=prefix.replace(' struct wr_iot_driver_owner wr_iot_driver_owner;', ' struct wr_iot_driver_owner wr_iot_driver_owner;\n struct {int active;} wr_iot_close_owner;')
prefix=prefix.replace('assert(!*(lock));*(lock)=1;', 'assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock);*(lock)=1;')
code=prefix+r'''
#include "precreated-idle-probe.h"
static int fault,reads;
static int rtnl_is_locked(void){return fault!=1;}
static int netif_running(PNET_DEV dev){return dev->running;}
static void read_reg(PRTMP_ADAPTER ad,unsigned address,unsigned *out){
 assert(ad->BcnRingLock&&!ad->wr_iot_transition_lock);reads++;
 *out=address==ARB_BCNQCR0?1:0;
 if(fault==3)*out=0xffffffffU;
}
#define RTMP_IO_READ32 read_reg
static int WrBeaconDmaOutstanding(PRTMP_ADAPTER ad,unsigned id){assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&id==2);return fault==4?1:0;}
static int WrBeaconTxSOutstanding(PRTMP_ADAPTER ad,unsigned id){
 assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&id==2);
 if(fault==6)assert(wr_iot_radio_request_reset_kind(&ad->wr_iot_transition,WR_RADIO_RESET_PDMA));
 if(fault==7)ad->wr_iot_control_users=1;
 if(fault==8)ad->wr_iot_transition.serial++;
 if(fault==9)ad->wr_iot_beacon_gates[2].generation++;
 if(fault==12)ad->wr_iot_close_owner.active=1;
 return fault==5?-1:0;
}
#include "mt7603-closed-observe.h"
#include "precreated-idle-probe-binding.inc"
int main(void){
 for(fault=0;fault<13;fault++){
  struct device main_dev={1},iot_dev={0};
  struct adapter storage={.mt7603=1,.flags=3,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  struct adapter *ad=&storage;struct wr_iot_precreated_idle_probe probe={0};
  ad->ApCfg.MBSSID[0].wdev.if_dev=&main_dev;ad->ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
  ad->ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
  unsigned long sequence=0;
  wr_iot_radio_transition_init(&ad->wr_iot_transition);
  ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=iot->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  if(fault==2)ad->wr_iot_control_users=1;
  if(fault==11)ad->wr_iot_close_owner.active=1;
  if(fault==10)ad->wr_iot_beacon_gates[2].accepting=1;
  reads=0;int result=wr_iot_precreated_idle_probe_driver(ad,&iot_dev,&probe,2);
  assert((result==0)==(fault==0));
  assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock&&main_dev.running);
  if(fault==8)assert(result==-EUCLEAN&&probe.active&&ad->wr_iot_control_poisoned);
  else assert(!probe.active);
  if(fault==1||fault==2||fault==11)assert(!reads);
 }
 puts("PASS actual initial-idle binding plus existing observer: privilege-owner refusal, unknown MMIO/DMA/TxS, reset/control/producer drift, disjoint locks and persistent foreign-ticket poison; register/ring results injected");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='iot-idle-binding-') as d:
    source=Path(d)/'check.c';binary=Path(d)/'check';source.write_text(code)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
