#!/usr/bin/env python3
"""Bind checked MAC multi-read to its exact pending write and retire one proof."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'mcu_config_mac_pending' not in m or 'mcu_config_mac_read' in m or actual!=m['merged_driver_sha256']:p.error('Expected unchanged isolated MAC-record candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed MAC read anchor: '+name+': '+old[:60])
 changes[name]=text.replace(old,new)
one('include/mcu/andes_core.h','    unsigned int wr_iot_config_owned;',
 '    unsigned int wr_iot_config_owned;\n    unsigned int wr_iot_config_mac_query,wr_iot_config_mac_generation;')
anchor='INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_mcu_config_mac_read(struct _RTMP_ADAPTER *ad,UINT32 address,UINT32 *value);')
one('mcu/andes_core.c','#include "wr-iot-mcu-config-rf-read.inc"',
 '#include "wr-iot-mcu-config-rf-read.inc"\n#include "wr-iot-mcu-config-mac-read.inc"')
one('mcu/andes_core.c', '''((msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS && msg->set_query==CMD_SET &&
                 msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE)||''',
 '''((msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS &&
                 (msg->set_query==CMD_SET||(msg->wr_iot_config_mac_query&&msg->set_query==CMD_QUERY))&&
                 msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE)||''')
name='include/wr-iot-mcu-config-transport.inc'
one(name,'int ready,left,checked,noreply,rfquery;INT32 result;',
 'int ready,left,checked,noreply,rfquery,macquery;INT32 result;')
one(name,' checked=msg->cmd_type==EXT_CID', ''' macquery=msg->wr_iot_config_mac_query&&msg->cmd_type==EXT_CID&&
  msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS&&msg->set_query==CMD_QUERY&&
  msg->need_wait&&msg->need_rsp&&msg->rsp_payload_len==32&&!msg->rsp_payload&&!msg->rsp_handler;
 if(macquery){query_generation=msg->wr_iot_config_mac_generation;query_stream=0;
  query_address=msg->wr_iot_config_mac_address;query_value=msg->wr_iot_config_mac_value;}
 checked=msg->cmd_type==EXT_CID''')
one(name,'(checked||noreply))||rfquery)&&','(checked||noreply))||rfquery||macquery)&&')
anchor=' if(ready&&rfquery){'
one(name,anchor,''' if(ready&&macquery){
  ready=ad->wr_iot_boot_config_unconfirmed&&msg->net_pkt&&GET_OS_PKT_LEN(msg->net_pkt)==12&&
   !wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt))&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+4)==query_address&&
   !wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+8)&&
   wr_iot_config_rf_record_matches(&ad->wr_iot_config_mac_pending,query_generation,
    ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
    0,query_address,query_value);
 }
'''+anchor)
one(name,'msg->wr_iot_checked=(checked||rfquery)?1:0;','msg->wr_iot_checked=(checked||rfquery||macquery)?1:0;')
anchor=' if(result!=NDIS_STATUS_SUCCESS){ad->wr_iot_boot_failed=1;ad->wr_iot_mcu_sender_owner.uncertain=1;}'
one(name,anchor,''' if(result==NDIS_STATUS_SUCCESS&&macquery){
  if(!ad->wr_iot_boot_config_unconfirmed||
     !wr_iot_config_rf_record_matches(&ad->wr_iot_config_mac_pending,query_generation,
      ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
      0,query_address,query_value))result=NDIS_STATUS_FAILURE;
  else {ad->wr_iot_config_mac_pending.active=0;ad->wr_iot_boot_config_unconfirmed--;}
 }
'''+anchor)
for name,direct in [('mcu/andes_mt.c',False),('include/wr-iot-mcu-rx-direct.inc',True)]:
 one(name,'if (msg->need_wait && wr_iot_config_multi_write_success(',
  'if (msg->need_wait && !msg->wr_iot_config_mac_query && wr_iot_config_multi_write_success(')
 text=changes.get(name,(src/name).read_text());anchor='                    if (msg->need_wait)\n                        RTMP_OS_COMPLETE(&msg->ack_done);'
 if text.count(anchor)!=1:p.error('Changed MAC RX completion: '+name)
 data='data' if direct else 'GET_OS_PKT_DATAPTR(net_pkt)';length='length' if direct else 'GET_OS_PKT_LEN(net_pkt)'
 inject='''                    if(msg->need_wait&&msg->wr_iot_config_mac_query&&
                       wr_iot_config_mac_read_matches(msg->cmd_type,msg->ext_cmd_type,msg->set_query==CMD_QUERY,
                        event_rxd->fw_rxd_1.field.eid,event_rxd->fw_rxd_2.field.ext_eid,
                        LENGTH>=sizeof(*event_rxd)?DATA+sizeof(*event_rxd):NULL,
                        LENGTH>=sizeof(*event_rxd)?LENGTH-sizeof(*event_rxd):0,
                        LENGTH,event_rxd->fw_rxd_0.field.length,sizeof(*event_rxd),
                        msg->wr_iot_config_mac_address,msg->wr_iot_config_mac_value))
                      msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;
'''.replace('LENGTH',length).replace('DATA',data)
 changes[name]=text.replace(anchor,inject+anchor)
name='mcu/andes_mt.c';text=changes[name];start=text.index('INT32 CmdMultiPleMacRegAccessRead(');end=text.index('\n}\n',start)+3;body=text[start:end];anchor='\tUINT32 Index;'
if body.count(anchor)!=1:p.error('Changed MAC read builder')
body=body.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(pAd->wr_iot_boot_active){
  if(!RegPair||Num!=1)return NDIS_STATUS_FAILURE;
  return wr_iot_mcu_config_mac_read(pAd,RegPair[0].Register,&RegPair[0].Value);
 }
#endif
''');changes[name]=text[:start]+body+text[end:]
changes['include/wr-iot-mcu-config-mac-read.inc']=Path(__file__).with_name('mcu-config-mac-read.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes};m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_mac_read']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'mac_proof_retirement':True,'normal_init_refusal_removed':False,'target_compiled':False,'runtime_verified':False};mp.write_text(json.dumps(m,indent=2)+'\n')
