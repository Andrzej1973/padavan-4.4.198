#!/usr/bin/env python3
"""Connect reviewed channel/TX-power/EFUSE extended replies to owned config transport."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'mcu_config_mac_read' not in m or 'mcu_config_ext' in m or actual!=m['merged_driver_sha256']:p.error('Expected unchanged isolated MAC-read candidate')
sdk=(src/'include/mcu/andes_mt.h').read_text()
for pattern in [r'EXT_CMD_CHANNEL_SWITCH\s*=\s*0x08',r'EXT_CMD_SET_TX_POWER_CTRL\s*=\s*0x11',r'EXT_CMD_EFUSE_BUFFER_MODE\s*=\s*0x21',r'EXT_EVENT_CMD_RESULT\s*=\s*0x0\b',r'UINT8 ucExTenCID;\s*UINT8 aucReserve\[3\];\s*UINT32 u4Status;']:
 if not re.search(pattern,sdk):p.error('Changed extended-result SDK contract: '+pattern)
mt=(src/'mcu/andes_mt.c').read_text();start=mt.index('static VOID CmdEfuseBufferModeRsp(');end=mt.index('\n}\n',start)
callback=mt[start:end]
if 'struct _EVENT_EXT_CMD_RESULT_T *EventExtCmdResult' not in callback or 'EventExtCmdResult->u4Status = le2cpu32(EventExtCmdResult->u4Status);' not in callback:p.error('Changed EFUSE response callback')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed extended config anchor '+name+': '+old[:70])
 changes[name]=text.replace(old,new)
one('include/mcu/andes_core.h','    unsigned int wr_iot_config_owned;',
 '    unsigned int wr_iot_config_owned;\n    unsigned int wr_iot_config_ext_result,wr_iot_config_submitted;')
name='include/wr-iot-mcu-config-transport.inc'
one(name,'int ready,left,checked,noreply,rfquery,macquery;INT32 result;',
 'int ready,left,checked,noreply,rfquery,macquery,extchecked;INT32 result;')
one(name,' checked=msg->cmd_type==EXT_CID', ''' extchecked=msg->wr_iot_config_ext_result&&msg->cmd_type==EXT_CID&&
  wr_iot_config_ext_command(msg->ext_cmd_type)&&msg->set_query==CMD_SET&&
  msg->need_wait&&msg->need_rsp&&msg->rsp_payload_len==8&&!msg->rsp_payload&&!msg->rsp_handler&&
  !msg->wr_iot_config_mac_query&&!msg->wr_iot_config_rf_query;
 checked=msg->cmd_type==EXT_CID''')
one(name,'||rfquery||macquery)&&','||rfquery||macquery||extchecked)&&')
one(name,'msg->wr_iot_checked=(checked||rfquery||macquery)?1:0;',
 'msg->wr_iot_checked=(checked||rfquery||macquery||extchecked)?1:0;')
one('mcu/andes_core.c','((msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS &&',
 '''((msg->wr_iot_config_ext_result && wr_iot_config_ext_command(msg->ext_cmd_type)&&
                 msg->set_query==CMD_SET&&msg->rsp_payload_len==8)||
                (msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS &&''')
for name,direct in [('mcu/andes_mt.c',False),('include/wr-iot-mcu-rx-direct.inc',True)]:
 data='data' if direct else 'GET_OS_PKT_DATAPTR(net_pkt)';length='length' if direct else 'GET_OS_PKT_LEN(net_pkt)'
 anchor='                    if (msg->need_wait)\n                        RTMP_OS_COMPLETE(&msg->ack_done);'
 inject='''                    if(msg->need_wait&&msg->wr_iot_config_ext_result&&
                       !msg->wr_iot_config_mac_query&&!msg->wr_iot_config_rf_query&&
                       wr_iot_config_ext_success(msg->cmd_type,msg->ext_cmd_type,msg->set_query==CMD_SET,
                        event_rxd->fw_rxd_1.field.eid,event_rxd->fw_rxd_2.field.ext_eid,
                        LENGTH>=sizeof(*event_rxd)?DATA+sizeof(*event_rxd):NULL,
                        LENGTH>=sizeof(*event_rxd)?LENGTH-sizeof(*event_rxd):0,
                        LENGTH,event_rxd->fw_rxd_0.field.length,sizeof(*event_rxd)))
                      msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;
'''.replace('LENGTH',length).replace('DATA',data)
 one(name,anchor,inject+anchor)
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
name='mcu/andes_mt.c';text=changes[name]
for function,kind in [('CmdChannelSwitch','INT32'),('CmdSetTxPowerCtrl','VOID'),('CmdEfusBufferModeSet','VOID')]:
 start=text.index(kind+' '+function+'(');end=text.index('\n}\n',start)+3;body=text[start:end]
 alloc=re.search(r'msg = AndesAllocCmdMsg\(pAd, (sizeof\([^;]+)\);',body)
 if not alloc or body.count('ret = AndesSendCmdMsg(pAd, msg);')!=1:p.error('Changed extended builder '+function)
 original=alloc.group();size=alloc.group(1)
 body=body.replace(original,guard+'\n msg = pAd->wr_iot_boot_active ? wr_iot_mcu_config_alloc(pAd,'+size+') : AndesAllocCmdMsg(pAd,'+size+');\n#else\n '+original+'\n#endif')
 init=re.search(r'AndesInitCmdMsg\(msg, P1_Q0, EXT_CID, CMD_SET, (EXT_CMD_\w+), TRUE, 0,\s*TRUE, TRUE, 8, NULL, (?:EventExtCmdResult|CmdEfuseBufferModeRsp)\);',body)
 if not init:p.error('Changed extended builder initializer '+function)
 original=init.group();ext=init.group(1)
 body=body.replace(original,guard+'\n if(msg->wr_iot_config_owned){\n  AndesInitCmdMsg(msg,P1_Q0,EXT_CID,CMD_SET,'+ext+',TRUE,0,FALSE,TRUE,8,NULL,NULL);\n  msg->wr_iot_config_ext_result=1;\n }else\n#endif\n '+original)
 body=body.replace('ret = AndesSendCmdMsg(pAd, msg);',guard+'\n ret = msg->wr_iot_config_owned ? wr_iot_mcu_config_send(pAd,msg) : AndesSendCmdMsg(pAd,msg);\n#else\n ret = AndesSendCmdMsg(pAd, msg);\n#endif')
 if function=='CmdEfusBufferModeSet':
  default='\tdefault:\n\t\tgoto error;'
  if body.count(default)!=1:p.error('Changed EFUSE default cancellation')
  body=body.replace(default,'\tdefault:\n'+guard+'\n  if(msg->wr_iot_config_owned){(void)wr_iot_mcu_config_cancel(pAd,msg);return;}\n#endif\n\t\tgoto error;')
 text=text[:start]+body+text[end:]
changes[name]=text
name='include/wr-iot-mcu-config-transport.inc';text=changes[name]
if text.count(' result=wr_iot_mcu_send_body(ad,msg);')!=1:p.error('Changed owned submission boundary')
text=text.replace(' result=wr_iot_mcu_send_body(ad,msg);',' msg->wr_iot_config_submitted=1;\n result=wr_iot_mcu_send_body(ad,msg);')
start=text.index('refuse:\n');cancel=text[start+len('refuse:\n'):];assert cancel.endswith('}\n')
text=text[:start]+'refuse:\n return wr_iot_mcu_config_cancel(ad,msg);\n}\n'
anchor='INT32 wr_iot_mcu_config_send(RTMP_ADAPTER *ad,struct cmd_msg *msg)'
helper='INT32 wr_iot_mcu_config_cancel(RTMP_ADAPTER *ad,struct cmd_msg *msg)\n{\n ULONG flags=0,owner_flags=0;\n if(!ad||!msg||msg->wr_iot_config_submitted)return NDIS_STATUS_FAILURE;\n'+cancel
changes[name]=text.replace(anchor,helper+anchor)
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);',
 'INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);\nINT32 wr_iot_mcu_config_cancel(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);')
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_ext']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'commands':['channel switch','TX power','EFUSE buffer mode'],'no_response_proof':False,'normal_init_refusal_removed':False,
 'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
