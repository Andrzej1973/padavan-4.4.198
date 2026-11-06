#!/usr/bin/env python3
"""Stage bounded MAC-write status decoding in both checked RX paths."""
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
 'mcu_boot_config_owner' not in m or 'mcu_config_result' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated config-owner candidate')
enums=(src/'include/mcu/andes_mt.h').read_text()
for name,value in [('EXT_CID','0xED'),('EXT_EVENT','0xED'),('EXT_CMD_MULTIPLE_REG_ACCESS','0x0E'),('EXT_EVENT_MULTI_CR_ACCESS','0x0E')]:
 if len(re.findall(r'\b'+name+r'\s*=\s*'+value+r'\b',enums,re.I))!=1:p.error('Changed configuration protocol: '+name)
changes={}
mt=(src/'mcu/andes_mt.c').read_text()
for callback in ['CmdMultipleMacRegAccessWriteCb','CmdMultipleRfRegAccessWriteCb']:
 start=mt.index('static VOID '+callback+'(');end=mt.index('\n}',start)
 if '(data + 20)' not in mt[start:end] or 'le2cpu32(EventMultiCRAccessWR->u4Status)' not in mt[start:end]:
  p.error('Changed configuration response layout: '+callback)
 pattern=r'AndesInitCmdMsg\(msg,\s*P1_Q0,\s*EXT_CID,\s*CMD_SET,\s*EXT_CMD_MULTIPLE_REG_ACCESS,\s*TRUE,\s*0,\s*TRUE,\s*TRUE,\s*32,\s*NULL,\s*'+callback+r'\);'
 if len(re.findall(pattern,mt))!=1:p.error('Changed configuration response size: '+callback)
name='include/rtmp.h';text=(src/name).read_text();anchor='#include "mcu-boot-result.h"'
if text.count(anchor)!=1:p.error('Changed result header anchor')
changes[name]=text.replace(anchor,anchor+'\n#include "mcu-config-result.h"')
changes['include/mcu-config-result.h']=Path(__file__).with_name('mcu-config-result.h').read_text()
for name,direct in [('mcu/andes_mt.c',False),('include/wr-iot-mcu-rx-direct.inc',True)]:
 text=(src/name).read_text();anchor='                        msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;'
 if text.count(anchor)!=1:p.error('Changed checked completion anchor: '+name)
 data='data' if direct else 'GET_OS_PKT_DATAPTR(net_pkt)'
 length='length' if direct else 'GET_OS_PKT_LEN(net_pkt)'
 changes[name]=text.replace(anchor,anchor+'''
                    if (msg->need_wait && wr_iot_config_multi_write_success(
                        msg->cmd_type,msg->ext_cmd_type,msg->set_query==CMD_SET,
                        event_rxd->fw_rxd_1.field.eid,event_rxd->fw_rxd_2.field.ext_eid,
                        '''+length+''' >= sizeof(*event_rxd) ? '''+data+''' + sizeof(*event_rxd) : NULL,
                        '''+length+''' >= sizeof(*event_rxd) ? '''+length+''' - sizeof(*event_rxd) : 0,
                        '''+length+''',event_rxd->fw_rxd_0.field.length,sizeof(*event_rxd)))
                        msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;''')
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_config_result']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashes,'command_admission':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
