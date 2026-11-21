#!/usr/bin/env python3
"""Record exact MAC no-response intent for a reviewed multi-register readback."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'mcu_config_rf_read' not in m or 'mcu_config_mac_pending' in m or actual!=m['merged_driver_sha256']:p.error('Expected unchanged isolated RF-read candidate')
enums=(src/'include/mcu/andes_mt.h').read_text();mt=(src/'mcu/andes_mt.c').read_text()
if not re.search(r'enum\s*\{\s*MAC_CR\s*,\s*RF_CR\s*,\s*\}',enums):p.error('Changed MAC/RF type numbering')
start=mt.index('static VOID CmdMultipleMacRegAccessReadCb(');end=mt.index('\n}',start)
if '(data + 20)' not in mt[start:end] or 'le2cpu32(EventMultiCRAccessRD->u4Addr)' not in mt[start:end] or 'le2cpu32(EventMultiCRAccessRD->u4Data)' not in mt[start:end]:p.error('Changed MAC response record layout')
start=mt.index('INT32 CmdMultiPleMacRegAccessRead(');end=mt.index('\n}\n',start)
pattern=r'AndesInitCmdMsg\(msg,\s*P1_Q0,\s*EXT_CID,\s*CMD_QUERY,\s*EXT_CMD_MULTIPLE_REG_ACCESS,\s*TRUE,\s*0,\s*TRUE,\s*TRUE,\s*\(12 \* Num\) \+ 20,'
if not re.search(pattern,mt[start:end]):p.error('Changed MAC multi-read protocol/length')
if 'wr_iot_config_mac_read_matches' not in (src/'include/mcu-config-result.h').read_text():p.error('Reviewed MAC decoder required')
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed MAC pending anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','struct wr_iot_config_rf_pending wr_iot_config_rf_pending;',
 'struct wr_iot_config_rf_pending wr_iot_config_rf_pending;\n struct wr_iot_config_rf_pending wr_iot_config_mac_pending;')
one('common/rtmp_init.c','memset(&pAd->wr_iot_config_rf_pending,0,sizeof(pAd->wr_iot_config_rf_pending));',
 'memset(&pAd->wr_iot_config_rf_pending,0,sizeof(pAd->wr_iot_config_rf_pending));\n        memset(&pAd->wr_iot_config_mac_pending,0,sizeof(pAd->wr_iot_config_mac_pending));')
one('include/mcu/andes_core.h','    unsigned int wr_iot_config_owned;',
 '    unsigned int wr_iot_config_owned;\n    unsigned int wr_iot_config_mac_write,wr_iot_config_mac_address,wr_iot_config_mac_value;')
one('include/wr-iot-mcu-boot-config-owner.inc','!ad->wr_iot_config_rf_pending.active&&!ad->wr_iot_config_rf_pending.poisoned&&',
 '!ad->wr_iot_config_rf_pending.active&&!ad->wr_iot_config_rf_pending.poisoned&&\n  !ad->wr_iot_config_mac_pending.active&&!ad->wr_iot_config_mac_pending.poisoned&&')
name='include/wr-iot-mcu-config-transport.inc';anchor=' if(ready&&noreply&&msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS){'
one(name,anchor,''' if(ready&&noreply&&msg->cmd_type==CMD_ACCESS_REG&&msg->ext_cmd_type==EXT_CMD_NA){
  ready=msg->wr_iot_config_mac_write&&msg->net_pkt&&GET_OS_PKT_LEN(msg->net_pkt)==8&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt))==msg->wr_iot_config_mac_address&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+4)==msg->wr_iot_config_mac_value&&
   wr_iot_config_rf_record(&ad->wr_iot_config_mac_pending,
    ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
    0,msg->wr_iot_config_mac_address,msg->wr_iot_config_mac_value);
 }
'''+anchor)
name='mcu/andes_mt.c';text=(src/name).read_text();start=text.index('INT32 CmdAccessRegWrite(');end=text.index('\n}\n',start)+3;body=text[start:end]
anchor='\tAndesAppendCmdMsg(msg, (char *)&access_reg, sizeof(access_reg));'
if body.count(anchor)!=1:p.error('Changed MAC write payload')
body=body.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(msg->wr_iot_config_owned){
  msg->wr_iot_config_mac_write=1;msg->wr_iot_config_mac_address=address;msg->wr_iot_config_mac_value=data;
 }
#endif
''');changes[name]=text[:start]+body+text[end:]
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes};m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_mac_pending']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'mac_read_admitted':False,'target_compiled':False,'runtime_verified':False};mp.write_text(json.dumps(m,indent=2)+'\n')
