#!/usr/bin/env python3
"""Record exact owned RF write intent before transmission; no proof clearing."""
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
 'mcu_config_noresponse' not in m or 'mcu_config_rf_pending' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated no-response candidate')
changes={}
if 'wr_iot_config_le32' not in (src/'include/mcu-config-result.h').read_text():
 p.error('Reviewed RF readback byte decoder required')
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed RF record anchor: '+name)
 changes[name]=text.replace(old,new)
one('include/rtmp.h','#include "mcu-config-result.h"',
 '#include "mcu-config-result.h"\n#include "mcu-config-rf-pending.h"')
one('include/rtmp.h','unsigned int wr_iot_boot_config_unconfirmed;',
 'unsigned int wr_iot_boot_config_unconfirmed;\n struct wr_iot_config_rf_pending wr_iot_config_rf_pending;')
one('common/rtmp_init.c','pAd->wr_iot_boot_config_unconfirmed=0;',
 'pAd->wr_iot_boot_config_unconfirmed=0;\n        memset(&pAd->wr_iot_config_rf_pending,0,sizeof(pAd->wr_iot_config_rf_pending));')
one('include/mcu/andes_core.h','    unsigned int wr_iot_config_owned;',
 '    unsigned int wr_iot_config_owned;\n    unsigned int wr_iot_config_rf_write,wr_iot_config_rf_stream,wr_iot_config_rf_address,wr_iot_config_rf_value;')
one('include/wr-iot-mcu-boot-config-owner.inc',
 'ready=owned&&success&&peer&&!ad->wr_iot_boot_config_unconfirmed&&wr_iot_mcu_boot_config_ready(ad,ticket,0);',
 'ready=owned&&success&&peer&&!ad->wr_iot_boot_config_unconfirmed&&\n  !ad->wr_iot_config_rf_pending.active&&!ad->wr_iot_config_rf_pending.poisoned&&\n  wr_iot_mcu_boot_config_ready(ad,ticket,0);')
name='include/wr-iot-mcu-config-transport.inc';anchor=' if(ready){\n  ad->wr_iot_mcu_sender_owner.inflight=1;'
one(name,anchor,''' if(ready&&noreply&&msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS){
  ready=msg->wr_iot_config_rf_write&&msg->net_pkt&&
   GET_OS_PKT_LEN(msg->net_pkt)==12&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt))==msg->wr_iot_config_rf_stream&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+4)==msg->wr_iot_config_rf_address&&
   wr_iot_config_le32(GET_OS_PKT_DATAPTR(msg->net_pkt)+8)==msg->wr_iot_config_rf_value&&
   wr_iot_config_rf_record(&ad->wr_iot_config_rf_pending,
    ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
    msg->wr_iot_config_rf_stream,msg->wr_iot_config_rf_address,msg->wr_iot_config_rf_value);
 }
'''+anchor)
name='mcu/andes_mt.c';text=(src/name).read_text();start=text.index('INT32 CmdRFRegAccessWrite(');end=text.index('\n}\n',start)+3;body=text[start:end]
anchor='\tAndesAppendCmdMsg(msg, (char *)&RFRegAccess, sizeof(RFRegAccess));'
if body.count(anchor)!=1:p.error('Changed RF request payload anchor')
body=body.replace(anchor,anchor+'''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(msg->wr_iot_config_owned){
  msg->wr_iot_config_rf_write=1;msg->wr_iot_config_rf_stream=RFIdx;
  msg->wr_iot_config_rf_address=Offset;msg->wr_iot_config_rf_value=Value;
 }
#endif
''')
changes[name]=text[:start]+body+text[end:]
changes['include/mcu-config-rf-pending.h']=Path(__file__).with_name('mcu-config-rf-pending.h').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_rf_pending']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'rf_query_admitted':False,'unconfirmed_clear_implemented':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
