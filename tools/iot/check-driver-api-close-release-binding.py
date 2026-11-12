#!/usr/bin/env python3
"""Exercise actual experimental release binding with injected progress/MMIO."""
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
base = (here / 'check-mt7603-closed-binding.c').read_text()
prefix = base[:base.index('static int rtnl=1;')]
prefix = prefix.replace('#include "driver-api-owner.h"',
                        '#include "driver-api-owner.h"\n#include "driver-api-close-release.h"')
prefix = prefix.replace(' struct wr_iot_driver_owner wr_iot_driver_owner;',
                        ' struct wr_iot_driver_owner wr_iot_driver_owner;\n'
                        ' struct wr_iot_driver_close_owner wr_iot_close_owner;\n'
                        ' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;')
prefix = prefix.replace('} *PRTMP_ADAPTER;', '} RTMP_ADAPTER,*PRTMP_ADAPTER;')
prefix = prefix.replace('assert(!*(lock));*(lock)=1;',
                        'assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock);*(lock)=1;')
code = prefix + r'''
#define WR_IOT_RA2_NO_HOST_MODE 1
static int fault,progress_calls,probe_calls;
static int rtnl_is_locked(void){return fault!=1;}
static INT wr_iot_driver_close_progress(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 assert(ad&&dev&&request&&!ad->BcnRingLock&&!ad->wr_iot_transition_lock);
 progress_calls++;
 return fault==2?-EINPROGRESS:0;
}
static INT wr_iot_mt7603_closed_probe(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct wr_iot_mbss_closed_probe *probe,unsigned long generation,
 unsigned long token,unsigned long serial)
{
 assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock);
 probe_calls++;
 if(fault==3)return -EAGAIN;
 probe->main_device=ad->net_dev;probe->iot_device=dev;
 probe->generation=generation;probe->open_token=token;probe->close_serial=serial;
 probe->ticket.epoch=1;probe->ticket.serial=5;probe->ticket.operation=WR_RADIO_BSS_OBSERVE;
 ad->wr_iot_transition.retired_serial=5;
 if(fault==4)ad->wr_iot_transition.reset_pending=1;
 if(fault==5)ad->wr_iot_beacon_gates[2].generation++;
 if(fault==6)ad->wr_iot_control_users=1;
 return 0;
}
#include "driver-api-close-release-binding.inc"
int main(void)
{
 for(fault=0;fault<9;fault++){
  struct device main_dev={1},iot_dev={0};
  RTMP_ADAPTER storage={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3},*ad=&storage;
  struct wr_iot_driver_close_request request={{1},1,2,3};
  ad->ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
  ad->wr_iot_beacon_gates[2].generation=7;
  wr_iot_radio_transition_init(&ad->wr_iot_transition);
  ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;
  unsigned long sequence=0;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  iot->published=1;iot->last_token=3;iot->close_serial=4;iot->close_stage=4;
  iot->close_epoch=1;iot->close_vendor_count=2;
  struct wr_iot_driver_close_owner *close=&ad->wr_iot_close_owner;
  close->active=close->consumed=close->retirement_module_transferred=1;
  close->reference_completed=close->synchronous_netdev_returned=1;
  close->device=&iot_dev;close->generation=2;close->open_token=3;
  close->ticket.epoch=1;close->ticket.serial=4;close->ticket.operation=WR_RADIO_BSS_CLOSE;
  struct wr_iot_driver_owner *open=&ad->wr_iot_driver_owner;
  open->receipt.valid=1;open->receipt.device=&iot_dev;open->receipt.epoch=1;
  open->receipt.generation=2;open->receipt.open_token=3;open->receipt.request_id[0]=1;
  if(fault==7)ad->wr_iot_beacon_gates[2].active=1;
  if(fault==8)open->active=1;
  progress_calls=probe_calls=0;
  int status=wr_iot_driver_close_release(ad,&iot_dev,&request);
  assert((status==0)==(fault==0));
  assert(close->active==(fault!=0));
  assert(!ad->BcnRingLock&&!ad->wr_iot_transition_lock);
  if(!fault){
   assert(progress_calls==1&&probe_calls==1);
   assert(!wr_iot_driver_close_release(ad,&iot_dev,&request));
   assert(progress_calls==1&&probe_calls==1);
   open->receipt.valid=0;
   assert(wr_iot_driver_close_release(ad,&iot_dev,&request)==-EAGAIN);
  }
 }
 puts("PASS actual experimental release binding: progress/probe refusal, reset/generation/control drift, disjoint locks, replay and replaced OPEN receipt; injected hardware and retirement");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-close-release-binding-') as scratch:
    source = Path(scratch) / 'test.c'
    executable = Path(scratch) / 'test'
    source.write_text(code)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(here), str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)

# Reuse the strict fixed-wire regression with the release opcode and codec.
wire_code = (here / 'check-driver-api-close-progress-wire.c').read_text()
wire_code = wire_code.replace('close-progress-wire.h', 'close-release-wire.h')
wire_code = wire_code.replace('close_progress_', 'close_release_').replace('wire[4]==13', 'wire[4]==14')
wire_code = wire_code.replace('progress opcode13', 'release opcode14')
with tempfile.TemporaryDirectory(prefix='wr-close-release-wire-') as scratch:
    source = Path(scratch) / 'wire.c'
    executable = Path(scratch) / 'wire'
    source.write_text(wire_code)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(here), str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
