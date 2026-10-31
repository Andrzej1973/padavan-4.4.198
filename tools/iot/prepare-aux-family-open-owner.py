#!/usr/bin/env python3
"""Bind existing main-radio APCLI/Monitor OPEN to exact registry claims."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
specs=[('ap/ap_apcli_inf.c','INT ApCli_VirtualIF_Open(',
 'ac4ac3bb1e050dcb1d76738430798f5a7bb2043ca0b0a38e494f061d959348ff',
 'WR_REF_FAMILY_APCLI','RTMP_AP_IoctlHandle','CMD_RTPRIV_IOCTL_APC_OPEN'),
 ('os/linux/rt_profile.c','INT Monitor_VirtualIF_Open(',
 '1febff40df60e43a9504577d06b52ac1834f8127b00c92e1c05806e15803772d',
 'WR_REF_FAMILY_MONITOR','RTMP_COM_IoctlHandle','CMD_RTPRIV_IOCTL_SNIFF_OPEN')]
changed={}
for name,sig,digest,family,ioctl,command in specs:
 raw=(src/name).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 s=raw.decode();start=s.index(sig);end=s.index('\n}',start)+2
 body=s[start:s.index('\n',start)]+'''
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;ULONG flags;
 int admitted,up,family_attempted=0,family_ok=0,finished,ready,owned,retain_pin=1;
 if(!dev_p)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev_p);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* First physical auxiliary open needs a separate startup/recovery owner. */
 admitted=VIRTUAL_IF_NUM(adapter)>0&&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,FAMILY,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev_p,&ticket,generation)==0;
 if(up){
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
  record=wr_iot_registry_find(adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,generation);
  family_attempted=record&&record->phase==WR_REF_RESERVED&&record->last_token==ticket.serial&&
   adapter->wr_iot_transition.busy==ticket.operation&&
   adapter->wr_iot_transition.serial==ticket.serial&&adapter->wr_iot_transition.epoch==ticket.epoch&&
   !adapter->wr_iot_transition.reset_pending&&!adapter->wr_iot_transition.retiring&&
   !adapter->wr_iot_transition.pm_suspending&&!adapter->wr_iot_transition.pm_suspended;
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  if(family_attempted)family_ok=IOCTL(adapter,NULL,COMMAND,0,dev_p,0)==NDIS_STATUS_SUCCESS;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,up&&family_ok);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&family_ok&&record&&
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,1,1,1,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,up&&ready,family_attempted,family_ok,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 /* Failed ndo_open has no guaranteed ndo_stop. Retain post-attempt pins. */
 if(!owned)return -1;
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev_p);
#endif
CARRIER
 return 0;
}'''
 body=body.replace('FAMILY',family).replace('IOCTL',ioctl).replace('COMMAND',command)
 carrier='#ifdef MTFWD\n RTMP_OS_NETDEV_CARRIER_OFF(dev_p);\n#endif' if family.endswith('APCLI') else ''
 body=body.replace('CARRIER',carrier)
 changed[name]=s[:start]+'#include "virtual-open-claim.h"\n'+body+s[end:]
shutil.copytree(src,out)
for name,s in changed.items():(out/name).write_text(s,encoding='utf-8',newline='\n')
print('Bound APCLI/Monitor claimed OPEN on existing radio; first-open/recovery still unbound')
