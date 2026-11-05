#!/usr/bin/env python3
"""Thread explicit optional boot tickets through actual firmware command builders."""
import argparse
import hashlib
import json
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_transport' not in manifest or 'mcu_boot_loader' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated owned-boot-transport candidate')
text=(src/'mcu/andes_mt.c').read_text()
method_start=text.index('static NDIS_STATUS AndesMTLoadFwMethod1(')
method_end=text.index('static NDIS_STATUS AndesMTLoadFwMethod2(',method_start)
scatter_start=text.index('static INT32 CmdFwScatters(')
scatter_end=text.index('\n}',scatter_start)+2
functions=('CmdRestartDLReq','CmdAddressLenReq','CmdFwScatter','CmdFwScatters','CmdFwStartReq')
edits=[]
for name in functions:
 matches=list(re.finditer(r'\b'+name+r'\(',text))
 if not matches:raise ValueError('Missing builder '+name)
 for m in matches:
  opening=m.end()-1;depth=1;end=opening+1
  while depth:
   if text[end]=='(':depth+=1
   if text[end]==')':depth-=1
   end+=1
  closing=end-1
  is_definition=text[text.rfind('\n',0,m.start())+1:m.start()].strip()=='static INT32'
  if is_definition:extra=', const struct wr_iot_mcu_boot_ticket *boot'
  elif method_start<m.start()<method_end or scatter_start<m.start()<scatter_end:extra=', boot'
  else:extra=', NULL'
  edits.append((closing,extra))
for pos,extra in sorted(edits,reverse=True):text=text[:pos]+extra+text[pos:]
for name in ('CmdRestartDLReq','CmdAddressLenReq','CmdFwScatter','CmdFwStartReq'):
 start=text.index('static INT32 '+name+'(');end=text.index('\n}',start)+2;body=text[start:end]
 body,count=re.subn(r'AndesAllocCmdMsg\(ad, (0|8|12|dl_len)\)',r'wr_iot_fw_command_alloc(ad, \1,boot)',body)
 if count!=1 or body.count('AndesSendCmdMsg(ad, msg)')!=1:raise ValueError('Changed builder '+name)
 body=body.replace('AndesSendCmdMsg(ad, msg)','wr_iot_fw_command_send(ad,msg,boot)')
 if name=='CmdAddressLenReq':body=body.replace('\tmsg = wr_iot_fw_command_alloc', '\tif (boot && address==ROM_PATCH_START_ADDRESS) return NDIS_STATUS_FAILURE;\n\tmsg = wr_iot_fw_command_alloc')
 text=text[:start]+body+text[end:]
helpers='''/* Ordinary callers carry NULL. Only Method1 may select an owned boot ticket. */
static struct cmd_msg *wr_iot_fw_command_alloc(RTMP_ADAPTER *ad,unsigned int length,
 const struct wr_iot_mcu_boot_ticket *boot)
{
 if(boot){
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
  return wr_iot_mcu_boot_alloc(ad,length,boot);
#else
  return NULL;
#endif
 }
 return AndesAllocCmdMsg(ad,length);
}
static INT32 wr_iot_fw_command_send(RTMP_ADAPTER *ad,struct cmd_msg *msg,
 const struct wr_iot_mcu_boot_ticket *boot)
{
 if(boot){
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
  return wr_iot_mcu_boot_send(ad,msg,boot);
#else
  AndesForceFreeCmdMsg(msg);return NDIS_STATUS_FAILURE;
#endif
 }
 return AndesSendCmdMsg(ad,msg);
}

'''
anchor='static INT32 CmdRestartDLReq('
text=text.replace(anchor,helpers+anchor,1)
start=text.index('static NDIS_STATUS AndesMTLoadFwMethod1(');end=text.index('static NDIS_STATUS AndesMTLoadFwMethod2(',start);body=text[start:end]
anchor='\tstruct MCU_CTRL *Ctl = &ad->MCUCtrl;';assert body.count(anchor)==1
body=body.replace(anchor,anchor+'''
 const struct wr_iot_mcu_boot_ticket *boot=NULL;
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(ad->wr_iot_boot_active)boot=&ad->wr_iot_boot_ticket;
#endif
#ifdef LOAD_FW_ONE_TIME
 /* Reusing live firmware cannot establish the required new boot epoch. */
 if(boot)return NDIS_STATUS_FAILURE;
#endif''')
text=text[:start]+body+text[end:]
header=(src/'include/mcu/andes_core.h').read_text();anchor='VOID AndesFreeCmdMsg(struct cmd_msg *msg);';assert header.count(anchor)==1
header=header.replace(anchor,anchor+'\nVOID AndesForceFreeCmdMsg(struct cmd_msg *msg);')
changes={'mcu/andes_mt.c':text,'include/mcu/andes_core.h':header}
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_loader']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'Method1 ticket propagation into actual builders; reservation/tasklet/epoch commit not bound','target_compiled':False,'runtime_verified':False,'normal_admission_rearmed':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
