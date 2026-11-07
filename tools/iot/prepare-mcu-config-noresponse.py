#!/usr/bin/env python3
"""Admit reviewed no-response writes, retaining an unresolved-effects count."""
import argparse
import hashlib
import json
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_config_transport' not in m or 'mcu_config_noresponse' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated config-transport candidate')
enums=(src/'include/mcu/andes_mt.h').read_text()
for name,value in [('CMD_ACCESS_REG','0xC2'),('EXT_CMD_RF_REG_ACCESS','0x02')]:
 if len(re.findall(r'\b'+name+r'\s*=\s*'+value+r'\b',enums,re.I))!=1:p.error('Changed no-response protocol: '+name)
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed no-response anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','unsigned int wr_iot_boot_config_state;',
 'unsigned int wr_iot_boot_config_state;\n unsigned int wr_iot_boot_config_unconfirmed;')
one('common/rtmp_init.c','pAd->wr_iot_boot_config_state=0;',
 'pAd->wr_iot_boot_config_state=0;pAd->wr_iot_boot_config_unconfirmed=0;')
one('include/wr-iot-mcu-boot-config-owner.inc',
 'ready=owned&&success&&peer&&wr_iot_mcu_boot_config_ready(ad,ticket,0);',
 'ready=owned&&success&&peer&&!ad->wr_iot_boot_config_unconfirmed&&wr_iot_mcu_boot_config_ready(ad,ticket,0);')
name='include/wr-iot-mcu-config-transport.inc'
one(name,'int ready,left;INT32 result;', 'int ready,left,checked,noreply;INT32 result;')
anchor=' RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);\n RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);\n ready=ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current&&\n       wr_iot_mcu_boot_config_ready(ad,&ticket,1)&&'
one(name,anchor,''' checked=msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS&&
  msg->need_wait&&msg->need_rsp&&msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE;
 noreply=!msg->need_wait&&!msg->need_rsp&&!msg->rsp_payload_len&&
  !msg->rsp_payload&&!msg->rsp_handler&&
  ((msg->cmd_type==CMD_ACCESS_REG&&msg->ext_cmd_type==EXT_CMD_NA)||
   (msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS));
'''+anchor)
one(name,'''       msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS&&
       msg->set_query==CMD_SET&&msg->need_wait&&msg->need_rsp&&!msg->need_retransmit&&
       msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE&&''',
 '''       msg->set_query==CMD_SET&&!msg->need_retransmit&&(checked||noreply)&&
       (!noreply||ad->wr_iot_boot_config_unconfirmed!=~0U)&&''')
one(name,'  msg->wr_iot_checked=1;',
 '''  msg->wr_iot_checked=checked?1:0;
  /* TX completion is not firmware execution/readback. Never clear here. */
  if(noreply)ad->wr_iot_boot_config_unconfirmed++;''')
name='mcu/andes_mt.c';text=(src/name).read_text()
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
for function,ad,payload,command,ext in [
 ('CmdAccessRegWrite','ad','struct _CMD_ACCESS_REG_T','CMD_ACCESS_REG','EXT_CMD_NA'),
 ('CmdRFRegAccessWrite','pAd','struct _CMD_RF_REG_ACCESS_T','EXT_CID','EXT_CMD_RF_REG_ACCESS')]:
 start=text.index('INT32 '+function+'(');end=text.index('\n}\n',start)+3;body=text[start:end]
 protocol=r'AndesInitCmdMsg\(msg,\s*P1_Q0,\s*'+command+r',\s*CMD_SET,\s*'+ext+r',\s*FALSE,\s*0,\s*FALSE,\s*FALSE,\s*0,\s*NULL,\s*NULL\);'
 if len(re.findall(protocol,body))!=1:p.error('Changed no-response builder: '+function)
 alloc=f'msg = AndesAllocCmdMsg({ad}, sizeof({payload}));';send=f'ret = AndesSendCmdMsg({ad}, msg);'
 if body.count(alloc)!=1 or body.count(send)!=1:p.error('Changed builder routing: '+function)
 body=body.replace(alloc,guard+f'\n msg = {ad}->wr_iot_boot_active ? wr_iot_mcu_config_alloc({ad},sizeof({payload})) : AndesAllocCmdMsg({ad},sizeof({payload}));\n#else\n '+alloc+'\n#endif')
 body=body.replace(send,guard+f'\n ret = msg->wr_iot_config_owned ? wr_iot_mcu_config_send({ad},msg) : AndesSendCmdMsg({ad},msg);\n#else\n '+send+'\n#endif')
 text=text[:start]+body+text[end:]
changes[name]=text
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_noresponse']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'unconfirmed_effects_block_finish':True,'readback_implemented':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
