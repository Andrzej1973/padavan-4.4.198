#!/usr/bin/env python3
"""Bind checked RF response to a saved write and retire only that proof."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'mcu_config_rf_pending' not in m or 'mcu_config_rf_read' in m or actual!=m['merged_driver_sha256']:p.error('Expected unchanged isolated RF-record candidate')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed RF read anchor: '+name+': '+old[:60])
 changes[name]=text.replace(old,new)
one('include/mcu/andes_core.h','    unsigned int wr_iot_config_owned;',
 '    unsigned int wr_iot_config_owned;\n    unsigned int wr_iot_config_rf_query,wr_iot_config_rf_generation;')
anchor='INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);'
one('include/mcu/andes_core.h',anchor,anchor+'\nINT32 wr_iot_mcu_config_rf_read(struct _RTMP_ADAPTER *ad,UINT32 stream,UINT32 address,UINT32 *value);')
one('mcu/andes_core.c','#include "wr-iot-mcu-config-transport.inc"',
 '#include "wr-iot-mcu-config-transport.inc"\n#include "wr-iot-mcu-config-rf-read.inc"')
one('mcu/andes_core.c', '''!(msg->wr_iot_config_owned && msg->cmd_type==EXT_CID &&
               msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS && msg->set_query==CMD_SET &&
               msg->need_rsp && msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE)''',
 '''!(msg->wr_iot_config_owned && msg->cmd_type==EXT_CID && msg->need_rsp &&
               ((msg->ext_cmd_type==EXT_CMD_MULTIPLE_REG_ACCESS && msg->set_query==CMD_SET &&
                 msg->rsp_payload_len==WR_IOT_CONFIG_MULTI_WRITE_SIZE)||
                (msg->wr_iot_config_rf_query && msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS &&
                 msg->set_query==CMD_QUERY && msg->rsp_payload_len==12)))''')
name='include/wr-iot-mcu-config-transport.inc'
one(name,'int ready,left,checked,noreply;INT32 result;',
 'int ready,left,checked,noreply,rfquery;INT32 result;\n unsigned int query_generation,query_stream,query_address,query_value;')
one(name,' checked=msg->cmd_type==EXT_CID', ''' rfquery=msg->wr_iot_config_rf_query&&msg->cmd_type==EXT_CID&&
  msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS&&msg->set_query==CMD_QUERY&&
  msg->need_wait&&msg->need_rsp&&msg->rsp_payload_len==12&&!msg->rsp_payload&&!msg->rsp_handler;
 query_generation=msg->wr_iot_config_rf_generation;query_stream=msg->wr_iot_config_rf_stream;
 query_address=msg->wr_iot_config_rf_address;query_value=msg->wr_iot_config_rf_value;
 checked=msg->cmd_type==EXT_CID''')
one(name,'msg->set_query==CMD_SET&&!msg->need_retransmit&&(checked||noreply)&&',
 '!msg->need_retransmit&&((msg->set_query==CMD_SET&&(checked||noreply))||rfquery)&&')
anchor=' if(ready&&noreply&&msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS){'
one(name,anchor,''' if(ready&&rfquery){
  ready=ad->wr_iot_boot_config_unconfirmed&&msg->net_pkt&&GET_OS_PKT_LEN(msg->net_pkt)==12&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt))==query_stream&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+4)==query_address&&
   !wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+8)&&
   wr_iot_config_rf_record_matches(&ad->wr_iot_config_rf_pending,query_generation,
    ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
    query_stream,query_address,query_value);
 }
'''+anchor)
one(name,'msg->wr_iot_checked=checked?1:0;', 'msg->wr_iot_checked=(checked||rfquery)?1:0;')
one(name,'  result=NDIS_STATUS_FAILURE;\n RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);',
 '  result=NDIS_STATUS_FAILURE;\n if(result==NDIS_STATUS_SUCCESS&&!wr_iot_mcu_boot_peer_matches(ad,ticket.peer_serial))\n  result=NDIS_STATUS_FAILURE;\n RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);')
anchor=' if(result!=NDIS_STATUS_SUCCESS){ad->wr_iot_boot_failed=1;ad->wr_iot_mcu_sender_owner.uncertain=1;}'
one(name,anchor,''' if(result==NDIS_STATUS_SUCCESS&&rfquery){
  if(!ad->wr_iot_boot_config_unconfirmed||
     !wr_iot_config_rf_record_matches(&ad->wr_iot_config_rf_pending,query_generation,
      ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
      query_stream,query_address,query_value))result=NDIS_STATUS_FAILURE;
  else {ad->wr_iot_config_rf_pending.active=0;ad->wr_iot_boot_config_unconfirmed--;}
 }
'''+anchor)
for name,direct in [('mcu/andes_mt.c',False),('include/wr-iot-mcu-rx-direct.inc',True)]:
 text=changes.get(name,(src/name).read_text());anchor='                    if (msg->need_wait)\n                        RTMP_OS_COMPLETE(&msg->ack_done);'
 if text.count(anchor)!=1:p.error('Changed RF RX completion: '+name)
 data='data' if direct else 'GET_OS_PKT_DATAPTR(net_pkt)';length='length' if direct else 'GET_OS_PKT_LEN(net_pkt)'
 inject='''                    if(msg->need_wait&&msg->wr_iot_config_rf_query&&
                       wr_iot_config_rf_read_matches(msg->cmd_type,msg->ext_cmd_type,msg->set_query==CMD_QUERY,
                        event_rxd->fw_rxd_1.field.eid,event_rxd->fw_rxd_2.field.ext_eid,
                        LENGTH>=sizeof(*event_rxd)?DATA+sizeof(*event_rxd):NULL,
                        LENGTH>=sizeof(*event_rxd)?LENGTH-sizeof(*event_rxd):0,
                        LENGTH,event_rxd->fw_rxd_0.field.length,sizeof(*event_rxd),
                        msg->wr_iot_config_rf_stream,msg->wr_iot_config_rf_address,msg->wr_iot_config_rf_value))
                      msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;
'''.replace('LENGTH',length).replace('DATA',data)
 changes[name]=text.replace(anchor,inject+anchor)
name='mcu/andes_mt.c';text=changes[name];start=text.index('INT32 CmdRFRegAccessRead(');end=text.index('\n}\n',start)+3;body=text[start:end];anchor='\tINT32 ret = 0;'
if body.count(anchor)!=1:p.error('Changed RF read builder')
body=body.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(pAd->wr_iot_boot_active)return wr_iot_mcu_config_rf_read(pAd,RFIdx,Offset,Value);
#endif
''');changes[name]=text[:start]+body+text[end:]
changes['include/wr-iot-mcu-config-rf-read.inc']=Path(__file__).with_name('mcu-config-rf-read.inc').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes};m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_rf_read']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'rf_proof_retirement':True,'normal_init_refusal_removed':False,'target_compiled':False,'runtime_verified':False};mp.write_text(json.dumps(m,indent=2)+'\n')
