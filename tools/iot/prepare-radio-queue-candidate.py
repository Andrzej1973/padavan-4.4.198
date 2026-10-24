#!/usr/bin/env python3
"""Assemble reviewed queue/ACK/adapter changes, not a complete/buildable driver tree.

Source is read-only. manifest.json is written last; absent manifest means an
incomplete preparation. This utility never installs into firmware sources.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('source',type=Path,help='exact pinned mt76x3 source directory')
p.add_argument('output',type=Path,help='new separate candidate bundle')
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:
    raise SystemExit('Output must be new and separate')
here=Path(__file__).resolve().parent
groups={
 'txs-status':('prepare-txs-status-candidate.py',['tx_rx/txs.c','include/mac/mac_mt/mt_mac.h','include/mac/mac.h','mac/mt_mac.c']),
 'checked-close':('prepare-checked-close.py',['common/rtmp_init_inf.c']),
 'task-retention':('prepare-task-join-retention.py',['os/linux/rt_linux.c','common/wsc.c']),
 'aux-refs':('prepare-auxiliary-open-refs.py',['ap/ap_apcli_inf.c','ap/ap_wds_inf.c']),
 'counter':('prepare-interface-count-guards.py',['common/cmm_cfg.c','include/wr-iot-virtual-down.inc','include/wr-iot-netdev-registration.inc']),
 'enqueue':('prepare-checked-enqueue.py',['common/cmm_cmd.c','checked-enqueue.inc']),
 'queue':('prepare-queue-cleanup.py',['common/rtmp_init.c','os/linux/rt_rbus_pci_drv.c',
          'include/queued-result.h','include/queued-cleanup.h','include/queued-work.h']),
 'adapter':('prepare-radio-adapter-candidate.py',['include/rtmp.h','common/rtmp_init.c',
             'os/linux/rt_profile.c','os/linux/rt_main_dev.c','include/radio-transition.h','include/interface-reference.h','include/interface-registry.h','include/mt7603-main-observe.h',
             'include/wr-iot-physical-close-result.inc','adapter-init.inc','adapter-free.inc','check-main-close.c','check-main-open.c']),
 'reset':('prepare-reset-admission.py',['common/cmm_mac_pci.c','include/wr-iot-reset-admission.inc']),
 'mcu':('prepare-mcu-radio-result.py',['include/mcu/andes_core.h',
        'mcu/andes_core.c','mcu/andes_mt.c','mcu/wr-iot-radio-result.h','checked-ack-branch.inc']),
}
source_names=['tx_rx/txs.c','tx_rx/wdev.c','ap/ap.c','include/mac/mac_mt/mt_mac.h','include/mac/mac.h','mac/mt_mac.c','common/rtmp_init_inf.c','common/wsc.c','os/linux/rt_linux.c','ap/ap_apcli_inf.c','ap/ap_wds_inf.c','common/cmm_cfg.c','common/cmm_cmd.c','common/rtmp_init.c','os/linux/rt_rbus_pci_drv.c',
              'include/mcu/andes_core.h','mcu/andes_core.c','mcu/andes_mt.c',
              'include/rtmp.h','os/linux/rt_profile.c','os/linux/rt_main_dev.c','common/cmm_mac_pci.c','common/cmm_mac_sdio.c','common/cmm_data_pci.c']
originals={name:(root/name).read_bytes() for name in source_names}
inputs=[here/script for script,_ in groups.values()]
inputs += [Path(__file__).resolve()]
inputs += [here/name for name in ('queued-result.h','queued-cleanup.h','queued-work.h','radio-result.h')]
inputs += [here/'prepare-radio-error-candidates.py',here/'prepare-mbss-lifecycle-candidate.py']
inputs += [here/'prepare-beacon-txs-callback-ledger.py',here/'prepare-txs-claimed-slot.py']
inputs += [here/'prepare-txs-handler-snapshot.py']
inputs += list(here.glob('prepare-*-check.py'))
inputs += [here/'checked-close-host-fixture.c.in',here/'physical-close-result.inc',here/'virtual-down-checked.inc',here/'interface-reference.h',here/'interface-registry.h',here/'netdev-registration.inc',here/'mbss-close-checked.inc']
inputs += [here/'checked-radio-off-builder.inc',here/'radio-transition.h',here/'mt7603-main-observe.h',here/'reset-admission.inc',here/'mbss-open-admission.inc']
tool_bytes={path:path.read_bytes() for path in inputs}
out.mkdir(parents=True)
records=[];seen=set();manifests={}
for group,(script,names) in groups.items():
    stage=out/'stages'/group
    stage.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(here/script),str(root),str(stage)],check=True)
    manifests[group]=json.loads((stage/'manifest.json').read_text())
    if manifests[group]['production_installed'] is not False:
        raise SystemExit('Stage unexpectedly claims installation')
    for name in names:
        data=(stage/name).read_bytes()
        target=out/'driver'/name
        if name in seen:
            if group!='adapter' or name!='common/rtmp_init.c':
                raise SystemExit('Overlapping stage output: '+name)
            # The sole reviewed overlap: adapter init before publication,
            # disjoint from queue dispatch/cleanup in the same source file.
            baseline=originals[name].decode('utf-8').replace('\r\n','\n')
            anchor='\t\t*ppAdapter = (VOID *)pAd;'
            insertion=(stage/'adapter-init.inc').read_text(encoding='utf-8')
            if baseline.count(anchor)!=1 or data.decode('utf-8').replace('\r\n','\n')!=baseline.replace(anchor,insertion+anchor,1):
                raise SystemExit('Unreviewed adapter overlap delta')
            merged=target.read_text(encoding='utf-8')
            if merged.count(anchor)!=1 or 'wr_iot_radio_transition_init' in merged:
                raise SystemExit('Conflicting adapter publication edit')
            data=merged.replace(anchor,insertion+anchor,1).encode('utf-8')
            records=[r for r in records if r['path']!=name]
            record_stage='queue+adapter'
        else:
            record_stage=group
        seen.add(name)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        records.append({'path':name,'stage':record_stage,
                        'purpose':'fixture' if name.endswith('.inc') or name.startswith('check-') else 'driver',
                        'sha256':hashlib.sha256(data).hexdigest()})
# Compose the older beacon/error work instead of replacing its shared PCI
# source with a reset-wrapper-only version. Every overlap is reviewed below.
error_stage=out/'stages'/'radio-errors'
subprocess.run([sys.executable,str(here/'prepare-radio-error-candidates.py'),str(root),str(error_stage)],check=True)
errors=json.loads((error_stage/'manifest.json').read_text())
manifests['radio-errors']=errors

def selected(text,signature,count=1):
    if text.count(signature)!=count:raise SystemExit('Changed merge function: '+signature)
    start=text.index(signature);return text[start:text.index('\n}',start)+2]

for item in errors['files']:
    name=item['path'];data=(error_stage/name).read_bytes();target=out/'driver'/name
    original=(root/name).read_bytes()
    if hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()!=item['original_git_blob']:
        raise SystemExit('Error-stage original changed: '+name)
    originals.setdefault(name,original)
    if name in seen:
        if name not in ('common/cmm_mac_pci.c','os/linux/rt_linux.c'):raise SystemExit('Unreviewed radio/error overlap: '+name)
        base=original.decode('utf-8').replace('\r\n','\n')
        patched=data.decode('utf-8').replace('\r\n','\n')
        restored=patched;merged=target.read_text(encoding='utf-8')
        functions=([('PNET_DEV RtmpOSNetDevCreate(',1)] if name=='os/linux/rt_linux.c' else
                   [('VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd)',1),
                    ('VOID RT28xx_UpdateBeaconToAsic(',2)])
        for sig,count in functions:
            old,new=selected(base,sig,count),selected(patched,sig,count)
            restored=restored.replace(new,old,1)
            if sig.startswith('VOID PDMA'):
                old=old.replace(sig,'static VOID wr_iot_pdma_reset_raw(RTMP_ADAPTER *pAd)',1)
                new=new.replace(sig,'static VOID wr_iot_pdma_reset_raw(RTMP_ADAPTER *pAd)',1)
            if merged.count(old)!=1:raise SystemExit('Conflicting merged function: '+sig)
            merged=merged.replace(old,new,1)
        if restored!=base:raise SystemExit('Unreviewed radio/error delta: '+name)
        data=merged.encode('utf-8');records=[r for r in records if r['path']!=name]
        stage_name='task-retention+netdev-create' if name=='os/linux/rt_linux.c' else 'reset+radio-errors'
    else:stage_name='radio-errors'
    seen.add(name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    records.append({'path':name,'stage':stage_name,'purpose':'driver',
                    'sha256':hashlib.sha256(data).hexdigest()})

# Bind the reviewed MBSS construction path to pre-publication registration.
path=out/'driver/ap/ap_mbss.c'
text=path.read_text(encoding='utf-8')
old='RtmpOSNetDevAttach(pAd->OpMode, pDevNew, &netDevHook)'
if text.count(old)!=1:raise SystemExit('Changed MBSS attach binding')
text=text.replace(old,'wr_iot_netdev_attach_checked(pAd, pAd->OpMode, pDevNew, &netDevHook)',1)
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']=='ap/ap_mbss.c':
        record['stage']='radio-errors+registry-attach'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# A successful CR-disable ioctl must show the per-BSS queue/TBTT control
# bits cleared before the checked-close path can advance. Register readback
# does not retire RX TxS reports or prove that RF transmission has stopped.
text=path.read_text(encoding='utf-8')
sig='INT mbss_cr_disable(PNET_DEV pDev)'
old=selected(text,sig)
new=old.replace('UINT32 Value;','UINT32 Value, Readback;',1)
anchor=('        RTMP_IO_WRITE32(pAd, ARB_BCNQCR0, Value);\n'
        '    }\n\n    RTMP_SEM_UNLOCK(&pAd->BcnRingLock);')
readback=('        RTMP_IO_WRITE32(pAd, ARB_BCNQCR0, Value);\n'
          '        RTMP_IO_READ32(pAd, (bssid_reg_base + (BssId - 1) * (0x4)), &Readback);\n'
          '        if (Readback & (TBTT0_n_INT_EN | PRE_TBTT0_n_INT_EN)) {\n'
          '            RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n'
          '            return -1;\n'
          '        }\n'
          '        RTMP_IO_READ32(pAd, ARB_BCNQCR0, &Readback);\n'
          '        if (Readback & (0x1U << (BssId + 15))) {\n'
          '            RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n'
          '            return -1;\n'
          '        }\n'
          '    }\n\n    RTMP_SEM_UNLOCK(&pAd->BcnRingLock);')
if old.count('UINT32 Value;')!=1 or old.count(anchor)!=1:
    raise SystemExit('Changed MBSS CR-disable readback anchor')
new=new.replace(anchor,readback,1)
text=text.replace(old,new,1)
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']=='ap/ap_mbss.c':
        record['stage']+=' + cr-disable-readback'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# Preserve the existing reviewed abort/open repairs inside one raw wrapper.
path=out/'driver/ap/ap_mbss_inf.c'
text=path.read_text(encoding='utf-8');sig='INT MBSS_VirtualIF_Open(PNET_DEV pDev)'
old=selected(text,sig)
raw=old.replace(sig,'static INT wr_iot_mbss_open_raw(PNET_DEV pDev)',1)
text=text.replace(old,raw+'\n#include "wr-iot-mbss-open-admission.inc"\n',1)
path.write_text(text,encoding='utf-8')
fragment=(here/'mbss-open-admission.inc').read_bytes()
target=out/'driver/include/wr-iot-mbss-open-admission.inc';target.write_bytes(fragment)
records.append({'path':'include/wr-iot-mbss-open-admission.inc','stage':'mbss-admission',
                'purpose':'driver','sha256':hashlib.sha256(fragment).hexdigest()})
for record in records:
    if record['path']=='ap/ap_mbss_inf.c':
        record['stage']='radio-errors+mbss-admission'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# Keep checked MBSS close separate until mandatory ndo_stop recovery is bound.
path=out/'driver/ap/ap_mbss_inf.c'
text=path.read_text(encoding='utf-8');sig='INT MBSS_VirtualIF_Close(PNET_DEV pDev)'
old=selected(text,sig)
text=text.replace(old,old+'\n#include "wr-iot-mbss-close-checked.inc"\n',1)
path.write_text(text,encoding='utf-8')
fragment=(here/'mbss-close-checked.inc').read_bytes()
(out/'driver/include/wr-iot-mbss-close-checked.inc').write_bytes(fragment)
records.append({'path':'include/wr-iot-mbss-close-checked.inc','stage':'mbss-checked-close','purpose':'driver','sha256':hashlib.sha256(fragment).hexdigest()})
for record in records:
    if record['path']=='ap/ap_mbss_inf.c':
        record['stage']='radio-errors+mbss-admission+checked-close'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# Expose the MAC_TX_INFO reservation generation from the beacon builder while
# preserving its existing callers. The legacy RTMP/RLT variant has no TxS
# reservation and returns zero. No submit/rollback caller is bound here.
path=out/'driver/ap/ap_connect.c'
text=path.read_text(encoding='utf-8')
sig='VOID write_tmac_info_beacon('
if text.count(sig)!=2:raise SystemExit('Changed beacon builder variants')
first_start=text.index(sig);first_end=text.index('\n}',first_start)+2
second_start=text.index(sig,first_end);second_end=text.index('\n}',second_start)+2
first=text[first_start:first_end];second=text[second_start:second_end]
anchor='\twrite_tmac_info(pAd, tmac_buf, &mac_info, BeaconTransmit);'
if first.count(anchor)!=1 or second.count(anchor)!=1:
    raise SystemExit('Changed beacon builder output')
first=first.replace(sig,'UINT32 write_tmac_info_beacon(',1).replace(
    'ULONG frmLen)','ULONG frmLen, UINT8 *ReservedPid)',1).replace(
    anchor,anchor+'\n\tif (ReservedPid)\n\t\t*ReservedPid = mac_info.TxSReservationPid;\n\treturn mac_info.TxSReservationGeneration;',1)
second=second.replace(sig,'UINT32 write_tmac_info_beacon(',1).replace(
    'ULONG frmLen)','ULONG frmLen, UINT8 *ReservedPid)',1).replace(
    anchor,'\tif (ReservedPid)\n\t\t*ReservedPid = 0;\n'+anchor,1)
if not second.endswith('\n}'):
    raise SystemExit('Changed legacy beacon builder end')
second=second[:-2]+'\n\treturn 0;\n}'
text=text[:second_start]+second+text[second_end:]
text=text[:first_start]+first+text[first_end:]
old_call='\twrite_tmac_info_beacon(pAd, apidx, tmac_info, &BeaconTransmit, FrameLen);'
if text.count(old_call)!=2:raise SystemExit('Changed beacon builder calls')
text=text.replace(old_call,'\twrite_tmac_info_beacon(pAd, apidx, tmac_info, &BeaconTransmit, FrameLen, NULL);',1)
call_start=text.index('VOID APUpdateBeaconFrame(')
head=text[:call_start];body=text[call_start:]
if body.count(old_call)!=1:raise SystemExit('Changed active beacon builder call')
body=body.replace('UCHAR *pBeaconFrame, *tmac_info;',
                  'UCHAR *pBeaconFrame, *tmac_info;\n\tWR_BCN_TXS_RESERVATION reservation = {0};',1)
body=body.replace(old_call,
                  '\treservation.generation = write_tmac_info_beacon(pAd, apidx, tmac_info, &BeaconTransmit, FrameLen, &reservation.pid);',1)
submit='RT28xx_UpdateBeaconToAsic(pAd, apidx, FrameLen, UpdatePos);'
if body.count(submit)!=1:raise SystemExit('Changed beacon submit call')
body=body.replace(submit,'RT28xx_UpdateBeaconToAsic(pAd, apidx, FrameLen, UpdatePos, reservation);',1)
text=head+body
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']=='ap/ap_connect.c':
        record['stage']='radio-errors+beacon-generation-output'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# Carry both reservation coordinates to the submit boundary without decoding
# a TMAC descriptor after the big-endian swap. Submission handling is not yet
# checked; the token is intentionally unused in all three ABI variants.
path=out/'driver/include/rtmp.h'
text=path.read_text(encoding='utf-8')
proto='VOID RT28xx_UpdateBeaconToAsic(\n\tIN RTMP_ADAPTER * pAd,\n\tIN INT apidx,\n\tIN ULONG BeaconLen,\n\tIN ULONG UpdatePos);'
if text.count(proto)!=1:raise SystemExit('Changed beacon submit prototype')
new_proto=('typedef struct _WR_BCN_TXS_RESERVATION {\n\tUINT8 pid;\n\tUINT32 generation;\n'
           '} WR_BCN_TXS_RESERVATION;\n\n'
           'VOID RT28xx_UpdateBeaconToAsic(\n\tIN RTMP_ADAPTER * pAd,\n\tIN INT apidx,\n'
           '\tIN ULONG BeaconLen,\n\tIN ULONG UpdatePos,\n'
           '\tIN WR_BCN_TXS_RESERVATION reservation);')
text=text.replace(proto,new_proto,1);path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']=='include/rtmp.h':
        record['stage']='adapter+beacon-reservation-abi'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

for name,expected in [('common/cmm_mac_pci.c',2),('common/cmm_mac_sdio.c',1)]:
    path=out/'driver'/name
    if name.endswith('sdio.c'):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(originals[name])
    text=path.read_text(encoding='utf-8')
    signature='VOID RT28xx_UpdateBeaconToAsic('
    if text.count(signature)!=expected:raise SystemExit('Changed beacon submit variants: '+name)
    for index in range(expected-1,-1,-1):
        starts=[];pos=0
        while True:
            pos=text.find(signature,pos)
            if pos<0:break
            starts.append(pos);pos+=len(signature)
        start=starts[index];end=text.index('\n}',start)+2
        func=text[start:end]
        if func.split('{',1)[0].count('UpdatePos)')!=1:
            raise SystemExit('Changed submit arguments: '+name)
        func=func.replace('UpdatePos)','UpdatePos,\n\tIN WR_BCN_TXS_RESERVATION reservation)',1)
        if name.endswith('sdio.c'):
            func=func.replace('{\n','{\n\t(void)reservation;\n',1)
        elif index==1:
            anchor='\tif (IS_MT76x2(pAd))'
            if func.count(anchor)!=1:raise SystemExit('Changed legacy beacon body')
            func=func.replace(anchor,'\t(void)reservation;\n\n'+anchor,1)
        text=text[:start]+func+text[end:]
    path.write_text(text,encoding='utf-8')
    previous=next((r for r in records if r['path']==name),None)
    if previous:
        previous['stage']+=' + beacon-reservation-abi'
        previous['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        records.append({'path':name,'stage':'beacon-reservation-abi',
                        'purpose':'driver','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

# The MT PCI branch admits only while holding the beacon ring lock. All
# rejected paths below precede a CPU-index publication; only those may cancel
# a matching TxS reservation. A late TxS/failed cancel remains unresolved.
name='common/cmm_mac_pci.c';path=out/'driver'/name
text=path.read_text(encoding='utf-8');sig='VOID RT28xx_UpdateBeaconToAsic('
old=selected(text,sig,2);new=old
def replace_mt(anchor,replacement):
    global new
    if new.count(anchor)!=1:raise SystemExit('Changed MT beacon admission anchor')
    new=new.replace(anchor,replacement,1)
replace_mt('\t\t\treturn;\n\t\tbcn_buf =',
           '\t\t\tgoto unsubmitted;\n\t\tbcn_buf =')
replace_mt('DBGPRINT(RT_DEBUG_ERROR, ("%s(): bcn_buf is NULL!\\n", __FUNCTION__));\n\t\treturn;',
           'DBGPRINT(RT_DEBUG_ERROR, ("%s(): bcn_buf is NULL!\\n", __FUNCTION__));\n\t\tgoto unsubmitted;')
gate='RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\t\treturn;'
if new.count(gate)!=2:raise SystemExit('Changed beacon pre-submit gates')
new=new.replace(gate,'RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\t\tgoto unsubmitted;')
kick='\t\tHAL_KickOutMgmtTx(pAd, Q_IDX_BCN, pkt, buf, len);'
replace_mt(kick,
           '#ifdef RTMP_PCI_SUPPORT\n'
           '\t\t/* The vendor GET_BCNRING_FREENO macro ends in a semicolon,\n'
           '\t\t * so compare the ring indices directly under BcnRingLock. */\n'
           '\t\tif (((pAd->BcnRing.TxCpuIdx + 1) % BCN_RING_SIZE) ==\n'
           '\t\t    pAd->BcnRing.TxSwFreeIdx ||\n'
           '\t\t    HAL_KickOutMgmtTx(pAd, Q_IDX_BCN, pkt, buf, len) != 0) {\n'
           '\t\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n'
           '\t\t\tgoto unsubmitted;\n'
           '\t\t}\n#else\n'+kick+'\n#endif')
replace_mt('\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t} else {',
           '\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\treturn;\n\t} else {')
replace_mt('\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): BeaconPkt is NULL!\\n", __FUNCTION__));\n\t}\n}',
           '\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): BeaconPkt is NULL!\\n", __FUNCTION__));\n'
           '\t}\n\tunsubmitted:\n'
           '\tif (pAd && reservation.generation &&\n'
           '\t    CancelTxSReservation(pAd, reservation.pid, reservation.generation) != 0)\n'
           '\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): beacon TxS reservation could not be cancelled\\n", __FUNCTION__));\n}')
text=text.replace(old,new,1);path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']==name:
        record['stage']+=' + locked-admission-and-pre-submit-cancel'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()

# Surface the enqueue decision to APUpdateBeaconFrame. 0 means the MT PCI
# kickout published its CPU index (not DMA/TxS completion); -1 means a known
# pre-publication rejection; -2 means that token cancellation itself failed.
path=out/'driver/include/rtmp.h';text=path.read_text(encoding='utf-8')
old='VOID RT28xx_UpdateBeaconToAsic(\n'
if text.count(old)!=1:raise SystemExit('Changed submit declaration return')
text=text.replace(old,'INT32 RT28xx_UpdateBeaconToAsic(\n',1)
path.write_text(text,encoding='utf-8')

path=out/'driver/ap/ap_connect.c';text=path.read_text(encoding='utf-8')
old='\tRT28xx_UpdateBeaconToAsic(pAd, apidx, FrameLen, UpdatePos, reservation);'
if text.count(old)!=1:raise SystemExit('Changed submit caller')
text=text.replace(old,
    '\tif (RT28xx_UpdateBeaconToAsic(pAd, apidx, FrameLen, UpdatePos, reservation) != 0)\n'
    '\t\treturn;',1)
path.write_text(text,encoding='utf-8')

path=out/'driver/common/cmm_mac_pci.c';text=path.read_text(encoding='utf-8')
sig='VOID RT28xx_UpdateBeaconToAsic('
if text.count(sig)!=2:raise SystemExit('Changed PCI submit return variants')
mt=selected(text,sig,2)
mt=mt.replace(sig,'INT32 RT28xx_UpdateBeaconToAsic(',1)
if mt.count('\tBCN_BUF_STRUC *bcn_buf = NULL;')!=1:
    raise SystemExit('Changed MT beacon declaration')
mt=mt.replace('\tBCN_BUF_STRUC *bcn_buf = NULL;',
              '#if defined(BCN_OFFLOAD_SUPPORT) && defined(RTMP_PCI_SUPPORT)\n'
              '#error "IoT beacon TxS rollback requires an MCU-offload ownership path"\n'
              '#endif\n\tBCN_BUF_STRUC *bcn_buf = NULL;',1)
for old,new in [
    ('if (!pAd) return;','if (!pAd) return -1;'),
    ('\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\treturn;',
     '\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n\t\treturn 0;'),
    ('\tif (pAd && reservation.generation &&\n'
     '\t    CancelTxSReservation(pAd, reservation.pid, reservation.generation) != 0)\n'
     '\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): beacon TxS reservation could not be cancelled\\n", __FUNCTION__));',
     '\tif (pAd && reservation.generation &&\n'
     '\t    CancelTxSReservation(pAd, reservation.pid, reservation.generation) != 0) {\n'
     '\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): beacon TxS reservation could not be cancelled\\n", __FUNCTION__));\n'
     '\t\treturn -2;\n\t}\n\treturn -1;')]:
    if mt.count(old)!=1:raise SystemExit('Changed MT submit result branch')
    mt=mt.replace(old,new,1)
text=text.replace(selected(text,sig,2),mt,1)
legacy=selected(text,sig)
legacy=legacy.replace(sig,'INT32 RT28xx_UpdateBeaconToAsic(',1)
if legacy.count('return;')!=2:raise SystemExit('Changed legacy submit exits')
legacy=legacy.replace('return;','return -1;')
if not legacy.endswith('\n}'):raise SystemExit('Changed legacy submit end')
legacy=legacy[:-2]+'\n\treturn 0;\n}'
text=text.replace(selected(text,sig),legacy,1)
path.write_text(text,encoding='utf-8')

path=out/'driver/common/cmm_mac_sdio.c';text=path.read_text(encoding='utf-8')
sig='VOID RT28xx_UpdateBeaconToAsic('
func=selected(text,sig)
func=func.replace(sig,'INT32 RT28xx_UpdateBeaconToAsic(',1)
if func.count('\t(void)reservation;')!=1:raise SystemExit('Changed SDIO stub')
func=func.replace('\t(void)reservation;',
                  '\t(void)reservation;\n\treturn -1;',1)
text=text.replace(selected(text,sig),func,1)
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path'] in ('include/rtmp.h','ap/ap_connect.c','common/cmm_mac_pci.c','common/cmm_mac_sdio.c'):
        record['stage']+=' + submit-result-abi'
        record['sha256']=hashlib.sha256((out/'driver'/record['path']).read_bytes()).hexdigest()

# The shared PCI kickout must report DMA mapping failure before it mutates a
# ring cell. Its caller still has to check the result and settle its token.
name='common/cmm_data_pci.c';original=originals[name]
blob=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
if blob!='646beb40bc7acb8ee861190b717f8c9a465d0fae':
    raise SystemExit('Changed pinned PCI kickout source')
text=original.decode('utf-8')
sig='int RtmpPCIMgmtKickOut('
old=selected(text,sig)
new=old.replace('\tRTMP_DMACB *dma_buf;',
                '\tRTMP_DMACB *dma_buf;\n\tra_dma_addr_t mapped_pa;',1)
map_anchor='#ifdef RT_BIG_ENDIAN\n\tpDestTxD = (TXD_STRUC *)dma_buf->AllocVa;'
if new.count(map_anchor)!=1:raise SystemExit('Changed PCI map placement')
new=new.replace(map_anchor,
                '\tmapped_pa = PCI_MAP_SINGLE(pAd, frm_buf, pkt_len, 0, RTMP_PCI_DMA_TODEVICE);\n'
                '\tif (!mapped_pa)\n\t\treturn -1;\n\n'+map_anchor,1)
old_publish=('\tdma_buf->pNdisPacket = pPacket;\n'
             '\tdma_buf->pNextNdisPacket = NULL;\n'
             '\tdma_buf->PacketPa = PCI_MAP_SINGLE(pAd, frm_buf, pkt_len, 0, RTMP_PCI_DMA_TODEVICE);')
if new.count(old_publish)!=1:raise SystemExit('Changed PCI packet publication')
new=new.replace(old_publish,
                '\tdma_buf->pNdisPacket = pPacket;\n'
                '\tdma_buf->pNextNdisPacket = NULL;\n'
                '\tdma_buf->PacketPa = mapped_pa;',1)
text=text.replace(old,new,1)
# The DMA completion path also decodes a BSS index from the descriptor. An
# unknown own_mac must not silently become BSS 0, and no decoded index may
# reach MBSSID without a capacity/current-count bound. Ring reclamation still
# proceeds after a rejected state update.
sig='VOID RTMPHandleBcnDmaDoneInterrupt('
dma=selected(text,sig)
if dma.count('UCHAR bss_idx = 0;')!=1:raise SystemExit('Changed beacon DMA index init')
dma=dma.replace('UCHAR bss_idx = 0;', 'UCHAR bss_idx = 0xff;', 1)
# The ring may retire several descriptors in one call. A valid own_mac from
# one cell must never be reused when the next cell has an unknown own_mac.
owner_anchor='\t\t\ttxd_1 = (TMAC_TXD_1 *)(tmac_info + sizeof(TMAC_TXD_0));'
if dma.count(owner_anchor)!=1:raise SystemExit('Changed beacon DMA owner decode')
dma=dma.replace(owner_anchor,
                '\t\t\tbss_idx = 0xff;\n'+owner_anchor,1)
old_state=('\t\t\tpMbss = &pAd->ApCfg.MBSSID[bss_idx];\n'
           '//---Add by Carter for MT7603\n\n'
           '            if (pMbss->bcn_buf.bcn_state == BCN_TX_WRITE_TO_DMA)\n'
           '                pMbss->bcn_buf.bcn_state = BCN_TX_DMA_DONE;\n\n'
           '            AsicGetTsfTime(pAd, &Highpart, &Lowpart);\n'
           '            pMbss->BcnDmaDoneTime[pMbss->timer_loop] = Lowpart;//update TSF time to corresponding field.\n\n'
           '\t\t\tDBGPRINT(RT_DEBUG_INFO, ("%s():change state as idle\\n", __FUNCTION__));')
if dma.count(old_state)!=1:raise SystemExit('Changed beacon DMA BSS state block')
new_state=('\t\t\tif (bss_idx < pAd->ApCfg.BssidNum &&\n'
           '\t\t\t    bss_idx < MAX_MBSSID_NUM(pAd)) {\n'
           '\t\t\t\tpMbss = &pAd->ApCfg.MBSSID[bss_idx];\n'
           '\t\t\t\tif (pMbss->bcn_buf.bcn_state == BCN_TX_WRITE_TO_DMA)\n'
           '\t\t\t\t\tpMbss->bcn_buf.bcn_state = BCN_TX_DMA_DONE;\n'
           '\t\t\t\tAsicGetTsfTime(pAd, &Highpart, &Lowpart);\n'
           '\t\t\t\tpMbss->BcnDmaDoneTime[pMbss->timer_loop] = Lowpart;\n'
           '\t\t\t} else {\n'
           '\t\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): invalid beacon own_mac or BSS index\\n", __FUNCTION__));\n'
           '\t\t\t}')
dma=dma.replace(old_state,new_state,1)
text=text.replace(selected(text,sig),dma,1)
path=out/'driver'/name;path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(text,encoding='utf-8')
records.append({'path':name,'stage':'pci-dma-map-failure-result+beacon-dma-bss-bound+per-cell-owner-reset',
                'purpose':'driver','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

# Retry through the existing periodic command-thread path, outside queue lock.
# Completion is still contingent on timer/worker lifetime and must not be
# confused with a guaranteed bounded scheduler or adapter retirement proof.
path=out/'driver/common/rtmp_init.c'
text=path.read_text(encoding='utf-8');anchor='\t\t\t\t\t\tMlmePeriodicExec(pAd, cmdqelmt);'
if text.count(anchor)!=1:raise SystemExit('Changed periodic MLME dispatch hook')
text=text.replace(anchor,anchor+'\n#if defined(MT7603) && defined(DMA_RESET_SUPPORT)\n\t\t\t\t\t\twr_iot_radio_reset_drain(pAd);\n#endif',1)
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']=='common/rtmp_init.c':
        record['stage']='queue+adapter+reset-retry'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
# Keep the main PCI beacon deinit before the beacon lock is freed. Preserve
# the original non-PCI cleanup location; this does not yet quiesce producers
# or make a failed deinit safe.
name='os/linux/rt_profile.c';path=out/'driver'/name
text=path.read_text(encoding='utf-8')
start_anchor='\tNdisFreeSpinLock(&TimerSemLock);\n\n#ifdef MT_MAC\n#ifdef CONFIG_AP_SUPPORT\n'
if text.count(start_anchor)!=1:raise SystemExit('Changed main beacon teardown anchor')
start=text.index(start_anchor)+len('\tNdisFreeSpinLock(&TimerSemLock);\n\n')
end=text.index('#ifdef CONFIG_ATE',start)
block=text[start:end]
prefix='#ifdef MT_MAC\n#ifdef CONFIG_AP_SUPPORT\n'
suffix='#endif\n#endif\n'
if not block.startswith(prefix) or not block.rstrip().endswith(suffix.rstrip()):
    raise SystemExit('Changed main beacon teardown guards')
inner=block[len(prefix):block.rfind(suffix)]
free_anchor='#ifdef MT_MAC\n\tNdisFreeSpinLock(&pAd->BcnRingLock);\n#endif /* MT_MAC */'
if text.count(free_anchor)!=1:raise SystemExit('Changed beacon lock free anchor')
text=text.replace(free_anchor,
    '#if defined(MT_MAC) && defined(CONFIG_AP_SUPPORT)\n'+inner+'#endif\n\n'+free_anchor,1)
if text.count(block)!=1:raise SystemExit('Changed non-PCI beacon cleanup block')
text=text.replace(block,'#ifndef RTMP_MAC_PCI\n'+block+'#endif /* !RTMP_MAC_PCI */\n',1)
path.write_text(text,encoding='utf-8')
for record in records:
    if record['path']==name:
        record['stage']+=' + main-beacon-deinit-before-lock-free'
        record['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
# Make the PCI deinit IDLE check and STOP publication atomic with beacon DMA
# and TxS state updates. This is not a callback-drain or PID-reuse proof.
name='tx_rx/wdev.c';data=originals[name]
blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
if blob!='c3967f59f470bdaf3afdab8f3eec8fefba12aea7':
    raise SystemExit('Changed pinned beacon deinit source')
text=data.decode('utf-8');sig='INT wdev_bcn_buf_deinit('
func=selected(text,sig)
anchor='\tif (pAd->chipCap.hif_type == HIF_MT)\n\t{\n'
if func.count(anchor)!=1:raise SystemExit('Changed beacon deinit entry')
func=func.replace(anchor,anchor+
    '#ifdef RTMP_MAC_PCI\n\t\tULONG BcnFlags;\n'
    '\t\tRTMP_IRQ_LOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n',1)
anchor='\t\tif (bcn_info->bcn_state != BCN_TX_IDLE) {\n'
if func.count(anchor)!=1:raise SystemExit('Changed beacon deinit busy path')
func=func.replace(anchor,anchor+
    '#ifdef RTMP_MAC_PCI\n\t\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n',1)
anchor='\t\tbcn_info->bcn_state = BCN_TX_STOP;\n'
if func.count(anchor)!=1:raise SystemExit('Changed beacon deinit STOP path')
func=func.replace(anchor,anchor+
    '#ifdef RTMP_MAC_PCI\n\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n',1)
text=text.replace(selected(text,sig),func,1)
path=out/'driver'/name;path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(text,encoding='utf-8')
records.append({'path':name,'stage':'beacon-stop-state-lock',
                'purpose':'driver','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# Serialize the PCI AP start/stop beacon-state writes with DMA, TxS and deinit.
# This is a state lock stage, not a proof of producer or PID retirement.
name='ap/ap.c';data=originals[name]
blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
if blob!='e452c6f55b4dedb2703f4471f9fd2d2c7cb226ac':
    raise SystemExit('Changed pinned AP beacon state source')
text=data.decode('utf-8').replace('\r\n','\n')
for signature in ('VOID APStartUp(RTMP_ADAPTER *pAd)',
                  'VOID APStop(RTMP_ADAPTER *pAd)'):
    func=selected(text,signature)
    declaration='\tUCHAR idx;\n' if signature.startswith('VOID APStartUp') else '\tINT idx;\n'
    if func.count(declaration)!=1:raise SystemExit('Changed AP beacon index declaration')
    func=func.replace(declaration,declaration+
        '#if defined(MT_MAC) && defined(RTMP_MAC_PCI)\n'
        '\tULONG BcnFlags;\n#endif\n',1)
    state='\t\tpMbss->bcn_buf.bcn_state = BCN_TX_IDLE;\n'
    if func.count(state)!=1:raise SystemExit('Changed AP beacon IDLE writer')
    func=func.replace(state,
        '#if defined(MT_MAC) && defined(RTMP_MAC_PCI)\n'
        '\t\tRTMP_IRQ_LOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n'+state+
        '#if defined(MT_MAC) && defined(RTMP_MAC_PCI)\n'
        '\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n',1)
    text=text.replace(selected(text,signature),func,1)
path=out/'driver'/name;path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(text,encoding='utf-8')
records.append({'path':name,'stage':'ap-start-stop-beacon-state-lock',
                'purpose':'driver','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# The radio-error stage already holds BcnRingLock across final HW restart and
# IDLE publication. Extend that existing critical section to respect STOP.
name='hw_ctrl/cmm_asic_mt.c';data=originals[name]
blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
if blob!='a8c0c0ec59c7e51c88296111934597064cf36c4a':
    raise SystemExit('Changed pinned beacon recovery source')
path=out/'driver'/name
text=path.read_text(encoding='utf-8').replace('\r\n','\n')
sig='VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)'
func=selected(text,sig)
anchor=('\tRTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
        '\tif (!pMbss->bcn_buf.bBcnSntReq ||\n')
if func.count(anchor)!=1 or func.count('\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);')<2:
    raise SystemExit('Radio-error stage lost locked beacon restart')
func=func.replace(anchor,anchor+
    '\t    pMbss->bcn_buf.bcn_state == BCN_TX_STOP ||\n',1)
text=text.replace(selected(text,sig),func,1)
path.write_text(text,encoding='utf-8')
matches=[record for record in records if record['path']==name]
if len(matches)!=1:raise SystemExit('Missing single radio-error recovery record')
matches[0]['stage']+=' + beacon-recovery-stop-guard'
matches[0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
# The AP debug ioctl is compiled with DBG in the pinned AP config. Keep its
# direct state write within the same IRQ-safe lock and reject invalid BSS IDs.
name='ap/ap_cfg.c';data=originals[name]
blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
if blob!='17853ec17d577021ce876c5ec6d8909e27a7453b':
    raise SystemExit('Changed pinned beacon debug setter source')
path=out/'driver'/name
text=path.read_text(encoding='utf-8').replace('\r\n','\n')
sig='INT Set_BcnStateCtrl_Proc('
func=selected(text,sig)
old=('    UCHAR bcn_state;\n'
     '    POS_COOKIE pObj = (POS_COOKIE)pAd->OS_Cookie;\n'
     '    UCHAR apIndex = pObj->ioctl_if;\n'
     '    BSS_STRUCT *pMbss = NULL;\n')
new=('    LONG bcn_state;\n'
     '    POS_COOKIE pObj = (POS_COOKIE)pAd->OS_Cookie;\n'
     '    UCHAR apIndex;\n'
     '    BSS_STRUCT *pMbss = NULL;\n'
     '    ULONG BcnFlags;\n'
     '    UCHAR old_bcn_state = BCN_TX_IDLE;\n'
     '    BOOLEAN changed = FALSE;\n'
     '\n'
     '    if (!pObj)\n'
     '        return FALSE;\n'
     '    apIndex = pObj->ioctl_if;\n'
     '    if (apIndex >= pAd->ApCfg.BssidNum ||\n'
     '        apIndex >= MAX_MBSSID_NUM(pAd))\n'
     '        return FALSE;\n')
if func.count(old)!=1:raise SystemExit('Changed beacon debug setter declarations')
func=func.replace(old,new,1)
old=('    if (pMbss->bcn_buf.bcn_state != BCN_TX_IDLE) {\n'
     '        printk("MBSSID[%d], bcn_buf.bcn_state = %d, will change to %d\\n", apIndex, pMbss->bcn_buf.bcn_state, bcn_state);\n'
     '        RTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
     '        pMbss->bcn_buf.bcn_state = bcn_state;\n'
     '        RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n'
     '    }\n')
new=('    RTMP_IRQ_LOCK(&pAd->BcnRingLock, BcnFlags);\n'
     '    old_bcn_state = pMbss->bcn_buf.bcn_state;\n'
     '    if (old_bcn_state == BCN_TX_STOP ||\n'
     '        RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_HALT_IN_PROGRESS |\n'
     '                       fRTMP_ADAPTER_NIC_NOT_EXIST)) {\n'
     '        RTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n'
     '        return FALSE;\n'
     '    }\n'
     '    if (pMbss->bcn_buf.bcn_state != BCN_TX_IDLE) {\n'
     '        pMbss->bcn_buf.bcn_state = (UCHAR)bcn_state;\n'
     '        changed = TRUE;\n'
     '    }\n'
     '    RTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n'
     '    if (changed)\n'
     '        printk("MBSSID[%d], bcn_buf.bcn_state = %d, will change to %ld\\n", apIndex, old_bcn_state, bcn_state);\n')
if func.count(old)!=1:raise SystemExit('Changed beacon debug setter state block')
func=func.replace(old,new,1)
old_return='\n\n        return TRUE;\n}'
if func.count(old_return)!=1:raise SystemExit('Changed beacon debug setter return')
func=func.replace(old_return,'\n\n    return TRUE;\n}',1)
text=text.replace(selected(text,sig),func,1)
path.write_text(text,encoding='utf-8')
matches=[record for record in records if record['path']==name]
if len(matches)!=1:raise SystemExit('Missing single radio-error AP config record')
matches[0]['stage']+=' + beacon-debug-bound-and-lock'
matches[0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
# Keep the PID-to-callback gap accounted for in the same isolated bundle.
# This is a software snapshot only; it is not a late-report or RF barrier.
ledger_stage=out/'stages'/'beacon-txs-ledger'
subprocess.run([sys.executable,str(here/'prepare-beacon-txs-callback-ledger.py'),
                str(out/'driver'),str(ledger_stage)],check=True)
ledger_manifest=json.loads((ledger_stage/'manifest.json').read_text())
for name in ('tx_rx/txs.c','include/mac/mac_mt/mt_mac.h'):
    path=out/'driver'/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ledger_manifest['source_sha256'][name]:
        raise SystemExit('Beacon TxS ledger input drift: '+name)
    path.write_bytes((ledger_stage/name).read_bytes())
    matches=[record for record in records if record['path']==name]
    if len(matches)!=1:raise SystemExit('Missing single TxS ledger record: '+name)
    matches[0]['stage']+=' + beacon-callback-ledger'
    matches[0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
claim_stage=out/'stages'/'txs-claimed-slot'
subprocess.run([sys.executable,str(here/'prepare-txs-claimed-slot.py'),
                str(out/'driver'),str(claim_stage)],check=True)
claim_manifest=json.loads((claim_stage/'manifest.json').read_text())
for name in ('tx_rx/txs.c','include/mac/mac_mt/mt_mac.h'):
    path=out/'driver'/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=claim_manifest['source_sha256'][name]:
        raise SystemExit('Claimed TxS slot input drift: '+name)
    path.write_bytes((claim_stage/name).read_bytes())
    matches=[record for record in records if record['path']==name]
    if len(matches)!=1:raise SystemExit('Missing single TxS claim record: '+name)
    matches[0]['stage']+=' + claimed-slot-until-parser-exit'
    matches[0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
handler_stage=out/'stages'/'txs-handler-snapshot'
subprocess.run([sys.executable,str(here/'prepare-txs-handler-snapshot.py'),
                str(out/'driver'),str(handler_stage)],check=True)
handler_manifest=json.loads((handler_stage/'manifest.json').read_text())
handler_path=out/'driver'/'tx_rx/txs.c'
if hashlib.sha256(handler_path.read_bytes()).hexdigest()!=handler_manifest['source_sha256']:
    raise SystemExit('Type-1 handler snapshot input drift')
handler_path.write_bytes((handler_stage/'tx_rx/txs.c').read_bytes())
matches=[record for record in records if record['path']=='tx_rx/txs.c']
if len(matches)!=1:raise SystemExit('Missing single TxS handler record')
matches[0]['stage']+=' + type1-handler-snapshot'
matches[0]['sha256']=hashlib.sha256(handler_path.read_bytes()).hexdigest()
for name,data in originals.items():
    if (root/name).read_bytes()!=data:raise SystemExit('Source changed during assembly')
for path,data in tool_bytes.items():
    if path.read_bytes()!=data:raise SystemExit('Preparer/helper changed during assembly')
if manifests['txs-status'].get('beacon_txs_index_bounded') is not True:
    raise SystemExit('Beacon TxS callback index bound missing from staged driver')
if manifests['txs-status'].get('beacon_txs_state_lock_staged') is not True:
    raise SystemExit('Beacon TxS state lock missing from staged driver')
beacon_lock_forms={}
for record in records:
    name=record['path']
    if not name.endswith('.c'):
        continue
    source=(out/'driver'/name).read_text(encoding='utf-8')
    forms={
        'sem':bool(re.search(r'RTMP_SEM_LOCK\s*\(\s*&pAd->BcnRingLock',source)),
        'irq':bool(re.search(r'RTMP_IRQ_LOCK\s*\(\s*&pAd->BcnRingLock',source)),
    }
    if any(forms.values()):
        beacon_lock_forms[name]=forms
if not any(forms['sem'] for forms in beacon_lock_forms.values()):
    raise SystemExit('Expected existing beacon semaphore-form lock missing')
if not any(forms['irq'] for forms in beacon_lock_forms.values()):
    raise SystemExit('Expected beacon IRQ-form lock missing')
manifest={
 'schema':1,'source_revision':'c25283e915a2a00a763774dd255b14aff997285e',
 'source_git_blobs':{name:hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                     for name,data in originals.items()},
 'interface_count_guards_staged':True,'interface_count_serialization_proven':False,
 'complete_driver_tree':False,'production_installed':False,'issuer_bound':False,
 'radio_operation_bound':False,'target_compiled':False,'runtime_verified':False,
 'txs_status_validation_staged':True,'txs_status_lock_staged':True,'txs_occupied_pid_overwrite_prevented':True,
 'beacon_txs_callback_ledger_staged':True,
 'txs_claimed_slot_until_parser_exit_staged':True,
 'txs_type1_handler_snapshot_staged':True,
 'beacon_txs_snapshot_gate_staged':True,
 'beacon_txs_close_barrier_bound':False,
 'generation_tagged_pre_submit_cancel_staged':True,'beacon_cancel_caller_bound':True,
 'mac_tx_info_generation_output_staged':True,
 'beacon_builder_generation_output_staged':True,
 'beacon_reservation_token_passed_to_submit':True,
 'beacon_reservation_token_consumed_by_submit':True,
 'pci_dma_map_failure_return_staged':True,
 'beacon_locked_ring_admission_staged':True,
 'beacon_pre_submit_cancel_staged':True,
 'beacon_cancel_failure_quarantined':False,
 'beacon_txs_index_bounded':True,
 'beacon_dma_bss_index_bounded':True,
 'beacon_main_deinit_precedes_lock_free_staged':True,
 'beacon_txs_state_lock_staged':True,
 'beacon_stop_state_lock_staged':True,
 'ap_start_stop_beacon_state_lock_staged':True,
 'beacon_recovery_stop_guard_staged':True,
 'beacon_debug_bound_and_lock_staged':True,
 'beacon_debug_stop_guard_staged':True,
 'beacon_lock_forms_in_partial_bundle':beacon_lock_forms,
 'beacon_lock_forms_complete_tree':False,
 'beacon_lock_semantics_proven':False,
 'effective_multi_core_support':None,
 'beacon_lock_lifetime_proven':False,
 'beacon_submit_result_staged':True,
 'beacon_mcu_offload_combination_guarded':True,
 'txs_pid_reuse_safety_proved':False,
 'beacon_report_sn_matching_proved':False,
 'selective_bss_txs_retirement_proved':False,
 'bss_cr_disable_readback_staged':True,
 'bss_cr_disable_runtime_proved':False,
 'beacon_ring_admission_atomic':False,'beacon_pid_submission_accounted':False,
 'txs_callback_quiescence_proven':False,
 'mbss_open_admission_staged':True,'mbss_close_admission_staged':False,
 'radio_errors_merged':True,'reset_retry_hook_staged':True,'reset_retry_deadline_proven':False,
 'adapter_storage_staged':True,'adapter_retirement_proven':False,
 'lifecycle_exclusion_proven':False,'files':records,'stage_manifests':manifests,
 'preparer_inputs':{path.name:hashlib.sha256(data).hexdigest() for path,data in tool_bytes.items()},
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Assembled queue/ACK candidate changes; partial tree, no radio/production binding')
