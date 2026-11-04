#!/usr/bin/env python3
"""Prepare checked firmware-load results in an isolated candidate overlay."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def prepare(files):
    result=dict(files)
    def one(name,old,new):
        if result[name].count(old)!=1:raise ValueError('Changed boot-result anchor: '+name+': '+old)
        result[name]=result[name].replace(old,new)
    enums=result['include/mcu/andes_mt.h']
    for name,value in (('MT_TARGET_ADDRESS_LEN_REQ','0x01'),('MT_FW_START_REQ','0x02'),
                       ('MT_RESTART_DL_REQ','0xEF'),('MT_TARGET_ADDRESS_LEN_RSP','0x01'),
                       ('MT_FW_START_RSP','0x01'),('MT_RESTART_DL_RSP','0xEF')):
        if len(re.findall(r'\b'+name+r'\s*=\s*'+value+r'\b',enums,re.I))!=1:
            raise ValueError('Unreviewed firmware protocol: '+name)
    if not re.search(r'#define EXT_CMD_NA\s+0\b',result['include/mcu/andes_core.h']):
        raise ValueError('Unexpected init command extension')
    if len(re.findall(r'enum\s*\{\s*WIFI_FW_DOWNLOAD_SUCCESS\s*,',enums))!=1:
        raise ValueError('Unexpected firmware success status value')
    one('include/rtmp.h','#include "mcu-sender-owner.h"',
        '#include "mcu-sender-owner.h"\n#include "mcu-boot-result.h"')
    one('mcu/andes_core.c','msg->cmd_type != EXT_CID ||\n'
        '            msg->ext_cmd_type != EXT_CMD_RADIO_ON_OFF_CTRL ||',
        '((msg->cmd_type != EXT_CID ||\n'
        '              msg->ext_cmd_type != EXT_CMD_RADIO_ON_OFF_CTRL) &&\n'
        '             !wr_iot_mcu_boot_command(msg->cmd_type,msg->ext_cmd_type)) ||')
    wrapper='include/wr-iot-mcu-sender-wrapper.inc'
    one(wrapper,'radio_control=msg->cmd_type==EXT_CID &&\n'
        '               msg->ext_cmd_type==EXT_CMD_RADIO_ON_OFF_CTRL;',
        'radio_control=(msg->cmd_type==EXT_CID &&\n'
        '               msg->ext_cmd_type==EXT_CMD_RADIO_ON_OFF_CTRL)||\n'
        '               wr_iot_mcu_boot_command(msg->cmd_type,msg->ext_cmd_type);')
    one(wrapper,'/* Legacy radio callbacks only log status.',
        '/* Legacy radio and init-command callbacks only log status.')
    one(wrapper,'A failed legacy ON/OFF','A failed radio or init command')
    # Same locked completion/result storage as radio. No stack result pointer
    # or generic callback is introduced into this path.
    mt='mcu/andes_mt.c'
    anchor='                    if (msg->need_wait)\n                        RTMP_OS_COMPLETE(&msg->ack_done);'
    one(mt,anchor,
        '                    if (msg->need_wait && wr_iot_mcu_boot_success(\n'
        '                        msg->cmd_type,msg->ext_cmd_type,\n'
        '                        event_rxd->fw_rxd_1.field.eid,\n'
        '                        event_rxd->fw_rxd_2.field.ext_eid,\n'
        '                        GET_OS_PKT_LEN(net_pkt),event_rxd->fw_rxd_0.field.length,\n'
        '                        sizeof(*event_rxd)))\n'
        '                        msg->wr_iot_firmware_result=NDIS_STATUS_SUCCESS;\n'+anchor)
    for command,callback in (('MT_RESTART_DL_REQ','CmdReStartDLRsp'),
                              ('MT_TARGET_ADDRESS_LEN_REQ','CmdAddrellLenRsp'),
                              ('MT_FW_START_REQ','CmdStartDLRsp')):
        old=f'AndesInitCmdMsg(msg, P1_Q0, {command}, CMD_NA, EXT_CMD_NA, TRUE, 0, TRUE, TRUE, 0, NULL, {callback});'
        one(mt,old,old.replace('TRUE, 0, TRUE, TRUE','TRUE, 0, FALSE, TRUE'))
    for call in ('ret = CmdFwStartReq(ad, 1, FW_CODE_START_ADDRESS1);',
                 'ret = CmdFwStartReq(ad, 0, 0);'):
        one(mt,call,call+'\n\tif (ret) { Ctl->Stage = FW_NO_INIT; goto done; }')
    for name in ('include/mcu/andes_mt.h','include/mcu/andes_core.h'):
        result.pop(name)  # Reviewed protocol inputs, not changed source files.
    result['include/mcu-boot-result.h']=Path(__file__).with_name('mcu-boot-result.h').read_text()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path,nargs='?')
    p.add_argument('--install-isolated',action='store_true');a=p.parse_args()
    src=a.source.resolve();manifest=None;mp=src.with_name(src.name+'.manifest.json')
    if a.install_isolated:
        if a.output is not None:p.error('No output directory for isolated installation')
        raw=mp.read_bytes();manifest=json.loads(raw)
        actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest()
                for f in src.rglob('*') if f.is_file()}
        if (manifest.get('production_installed') is not False or
            manifest.get('target_compiled') is not False or
            'close_ack_order' not in manifest or actual!=manifest['merged_driver_sha256']):
            p.error('Expected unchanged isolated close-order candidate')
        out=src
    else:
        if a.output is None:p.error('Overlay output required')
        out=a.output.resolve()
        if out.exists() or src==out or src in out.parents or out in src.parents:
            p.error('Expected new separate overlay')
    names=('include/rtmp.h','include/mcu/andes_mt.h','include/mcu/andes_core.h',
           'mcu/andes_core.c','mcu/andes_mt.c','include/wr-iot-mcu-sender-wrapper.inc')
    changes=prepare({n:(src/n).read_text() for n in names})
    if manifest is None:out.mkdir(parents=True)
    for name,text in changes.items():
        path=out/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    hashes={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changes}
    report={
        'scope':'checked firmware-load response overlay only; rearm not authorized',
        'output_sha256':hashes,'target_compiled':False,
        'firmware_epoch_verified':False,'runtime_verified':False}
    if manifest is not None:
        manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
        report['input_manifest_sha256']=hashlib.sha256(raw).hexdigest()
        manifest['mcu_boot_result']=report;mp.write_text(json.dumps(manifest,indent=2)+'\n')
    else:(out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
