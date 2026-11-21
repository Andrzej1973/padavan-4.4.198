#!/usr/bin/env python3
"""Journal no-response EDCA/timing requests without granting execution proof."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',required=True,action='store_true')
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or 'mcu_config_ext' not in m or 'mcu_config_timing' in m or actual!=m['merged_driver_sha256']:p.error('Expected unchanged extended-config candidate')
sdk=(src/'include/mcu/andes_mt.h').read_text()
for pattern in [r'EXT_CMD_ID_EDCA_SET\s*=\s*0x27',r'EXT_CMD_ID_SLOT_TIME_SET\s*=\s*0x28',r'#define CMD_EDCA_AC_MAX 4']:
 if not re.search(pattern,sdk):p.error('Changed timing protocol '+pattern)
changes={}
def one(name,old,new):
 text=changes.get(name,(src/name).read_text())
 if text.count(old)!=1:p.error('Changed timing anchor '+name+': '+old[:60])
 changes[name]=text.replace(old,new)
one('include/rtmp.h','#include "mcu-config-rf-pending.h"','#include "mcu-config-rf-pending.h"\n#include "mcu-config-timing-pending.h"')
one('include/rtmp.h','struct wr_iot_config_rf_pending wr_iot_config_mac_pending;',
 'struct wr_iot_config_rf_pending wr_iot_config_mac_pending;\n struct wr_iot_config_timing_pending wr_iot_config_edca_pending,wr_iot_config_slot_pending;')
one('common/rtmp_init.c','memset(&pAd->wr_iot_config_mac_pending,0,sizeof(pAd->wr_iot_config_mac_pending));',
 'memset(&pAd->wr_iot_config_mac_pending,0,sizeof(pAd->wr_iot_config_mac_pending));\n        memset(&pAd->wr_iot_config_edca_pending,0,sizeof(pAd->wr_iot_config_edca_pending));\n        memset(&pAd->wr_iot_config_slot_pending,0,sizeof(pAd->wr_iot_config_slot_pending));')
one('include/wr-iot-mcu-boot-config-owner.inc','!ad->wr_iot_config_mac_pending.active&&!ad->wr_iot_config_mac_pending.poisoned&&',
 '!ad->wr_iot_config_mac_pending.active&&!ad->wr_iot_config_mac_pending.poisoned&&\n  !ad->wr_iot_config_edca_pending.ticket.active&&!ad->wr_iot_config_edca_pending.ticket.poisoned&&\n  !ad->wr_iot_config_slot_pending.ticket.active&&!ad->wr_iot_config_slot_pending.ticket.poisoned&&')
one('include/mcu/andes_core.h','INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);',
 'INT32 wr_iot_mcu_config_send(struct _RTMP_ADAPTER *ad,struct cmd_msg *msg);\nINT32 wr_iot_mcu_config_fail(struct _RTMP_ADAPTER *ad);')
name='include/wr-iot-mcu-config-transport.inc'
one(name,'(msg->cmd_type==EXT_CID&&msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS));',
 '(msg->cmd_type==EXT_CID&&(msg->ext_cmd_type==EXT_CMD_RF_REG_ACCESS||\n     msg->ext_cmd_type==EXT_CMD_ID_EDCA_SET||msg->ext_cmd_type==EXT_CMD_ID_SLOT_TIME_SET)));')
anchor=' if(ready){\n  ad->wr_iot_mcu_sender_owner.inflight=1;'
one(name,anchor,''' if(ready&&noreply&&msg->cmd_type==EXT_CID&&
    (msg->ext_cmd_type==EXT_CMD_ID_EDCA_SET||msg->ext_cmd_type==EXT_CMD_ID_SLOT_TIME_SET)){
  ready=msg->net_pkt&&wr_iot_config_timing_record(
   msg->ext_cmd_type==EXT_CMD_ID_EDCA_SET?&ad->wr_iot_config_edca_pending:&ad->wr_iot_config_slot_pending,
   ticket.peer_serial,ticket.radio_serial,ticket.radio_epoch,ticket.close_serial,ticket.close_epoch,
   msg->ext_cmd_type,GET_OS_PKT_DATAPTR(msg->net_pkt),GET_OS_PKT_LEN(msg->net_pkt));
 }
'''+anchor)
one(name,'struct cmd_msg *wr_iot_mcu_config_alloc', '''INT32 wr_iot_mcu_config_fail(RTMP_ADAPTER *ad)
{
 ULONG flags=0,owner_flags=0;
 if(!ad)return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_SPIN_LOCK_IRQSAVE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 if(ad->wr_iot_boot_config_state==1&&ad->wr_iot_boot_config_task==current)ad->wr_iot_boot_failed=1;
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ad->wr_iot_mcu_sender_lock,&owner_flags);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return NDIS_STATUS_FAILURE;
}
struct cmd_msg *wr_iot_mcu_config_alloc''')
name='mcu/andes_mt.c';text=(src/name).read_text();guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
for function,allocation in [('CmdEdcaParameterSet','size'),('CmdSlotTimeSet','sizeof(CMD_SLOT_TIME_SET_T)')]:
 start=text.index('INT32 '+function+'(');end=text.index('\n}\n',start)+3;body=text[start:end]
 alloc='msg = AndesAllocCmdMsg(pAd, '+allocation+');';send='ret = AndesSendCmdMsg(pAd, msg);'
 if body.count(alloc)!=1 or body.count(send)!=1:p.error('Changed timing builder '+function)
 if function=='CmdEdcaParameterSet':
  anchor='\tsize = 4+sizeof(TX_AC_PARAM_T)*EdcaParam.ucTotalNum;'
  if body.count(anchor)!=1:p.error('Changed EDCA length boundary')
  body=body.replace(anchor,guard+'\n if(pAd->wr_iot_boot_active&&(!EdcaParam.ucTotalNum||EdcaParam.ucTotalNum>CMD_EDCA_AC_MAX))return wr_iot_mcu_config_fail(pAd);\n#endif\n'+anchor)
 body=body.replace(alloc,guard+'\n msg=pAd->wr_iot_boot_active?wr_iot_mcu_config_alloc(pAd,'+allocation+'):AndesAllocCmdMsg(pAd,'+allocation+');\n#else\n '+alloc+'\n#endif')
 body=body.replace(send,guard+'\n ret=msg->wr_iot_config_owned?wr_iot_mcu_config_send(pAd,msg):AndesSendCmdMsg(pAd,msg);\n#else\n '+send+'\n#endif')
 text=text[:start]+body+text[end:]
changes[name]=text
changes['include/mcu-config-timing-pending.h']=Path(__file__).with_name('mcu-config-timing-pending.h').read_text()
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_timing']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,
 'proof_retirement':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
