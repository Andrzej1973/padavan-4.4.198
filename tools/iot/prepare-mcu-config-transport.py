#!/usr/bin/env python3
"""Route reviewed MAC/RF multi-write builders through owned config transport."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False or
 'mcu_config_result' not in m or 'mcu_config_transport' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated config-result candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed config transport anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/wr-iot-mcu-boot-config-owner.inc',
 'const struct wr_iot_mcu_boot_ticket *t)\n{', 'const struct wr_iot_mcu_boot_ticket *t,unsigned int messages)\n{')
one('include/wr-iot-mcu-boot-config-owner.inc','!ad->wr_iot_mcu_sender_owner.messages&&',
 'ad->wr_iot_mcu_sender_owner.messages==messages&&')
name='include/wr-iot-mcu-boot-config-owner.inc';changes[name]=changes[name].replace('wr_iot_mcu_boot_config_ready(ad,ticket)', 'wr_iot_mcu_boot_config_ready(ad,ticket,0)')
one('include/mcu/andes_core.h','    BOOLEAN wr_iot_checked;',
 '    unsigned int wr_iot_config_owned;\n    unsigned long wr_iot_config_peer_serial,wr_iot_config_radio_serial,wr_iot_config_radio_epoch,wr_iot_config_close_serial,wr_iot_config_close_epoch;\n    BOOLEAN wr_iot_checked;')
anchor='INT32 wr_iot_mcu_boot_config_begin(struct _RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *ticket);'
one('include/mcu/andes_core.h',anchor,anchor+'\nstruct cmd_msg *wr_iot_mcu_config_alloc(struct _RTMP_ADAPTER *ad,unsigned int length);\nINT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);')
one('mcu/andes_core.c','#include "wr-iot-mcu-boot-config-owner.inc"',
 '#include "wr-iot-mcu-boot-config-owner.inc"\n#include "wr-iot-mcu-config-transport.inc"')
one('mcu/andes_core.c','!wr_iot_mcu_boot_command(msg->cmd_type,msg->ext_cmd_type)) ||',
 '!wr_iot_mcu_boot_command(msg->cmd_type,msg->ext_cmd_type) &&\n             !(msg->wr_iot_config_owned && msg->cmd_type==EXT_CID &&\n               msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS && msg->set_query==CMD_SET &&\n               msg->need_rsp && msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE)) ||')
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
name='mcu/andes_mt.c';text=(src/name).read_text()
for function in ['CmdMultipleMacRegAccessWrite','CmdMultipleRfRegAccessWrite']:
 start=text.index('INT32 '+function+'(');end=text.index('\n}\n',start)+3;body=text[start:end]
 alloc='msg = AndesAllocCmdMsg(pAd, sizeof(CMD_MULTI_CR_ACCESS_T) * Num);'
 send='Ret = AndesSendCmdMsg(pAd, msg);'
 if body.count(alloc)!=1 or body.count(send)!=1:p.error('Changed config builder: '+function)
 body=body.replace(alloc,guard+'\n if(pAd->wr_iot_boot_active && (!Num || Num>MT_UPLOAD_FW_UNIT/sizeof(CMD_MULTI_CR_ACCESS_T)))return NDIS_STATUS_FAILURE;\n msg = pAd->wr_iot_boot_active ? wr_iot_mcu_config_alloc(pAd,sizeof(CMD_MULTI_CR_ACCESS_T)*Num) : AndesAllocCmdMsg(pAd,sizeof(CMD_MULTI_CR_ACCESS_T)*Num);\n#else\n '+alloc+'\n#endif')
 body=body.replace(send,guard+'\n Ret = msg->wr_iot_config_owned ? wr_iot_mcu_config_send(pAd,msg) : AndesSendCmdMsg(pAd,msg);\n#else\n '+send+'\n#endif')
 text=text[:start]+body+text[end:]
changes[name]=text
changes['include/wr-iot-mcu-config-transport.inc']=Path(__file__).with_name('mcu-config-transport.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_transport']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'commands':['MAC/RF synchronous multiple-register write'],'no_response_admitted':False,
 'config_owner_bound_to_init':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
